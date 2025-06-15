import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from loguru import logger
from weasyprint import HTML

from .models import (AvailableTrack, DailyRetooling, Inventory, Order, Parameters, ProductionDay,
                     ProductionDayPlate, UnitPrice, UnplacedPlate, UsedReadyPlate)
from .services.calculation import calculate_plan, clear_old_data
from .services.upd_1c import update_data
from .utils import handle_view_exception


@login_required(login_url='/admin/login/')
def get_date_range_from_request(request):
    date_from = request.GET.get('date_from')
    if not date_from:
        date_from = datetime.date.today().strftime('%Y-%m-%d')
    date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')
    date_to = request.GET.get('date_to')
    if date_to:
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d')
    return date_from, date_to


@handle_view_exception
@login_required(login_url='/admin/login/')
@logger.catch
def index(request):
    parameters = Parameters.get_solo()
    date_from, _ = get_date_range_from_request(request)
    date_to = date_from + datetime.timedelta(days=100)
    all_available_tracks = AvailableTrack.get_tracks(date_from, date_to)
    production_days = {}
    available_tracks = []

    padding_days = 14

    for track in all_available_tracks:
        if padding_days == 0:
            break
        production_days[track.date] = list(ProductionDay.objects.filter(date=track.date))
        available_tracks.append(track)

        if track.count and len(production_days[track.date]) == 0:
            padding_days -= 1

    plates_complete_dates = {}
    for plate in ProductionDayPlate.objects.all().prefetch_related('production_day'):
        plates_complete_dates[(plate.order, plate.name)] = plate.production_day.date

    # Get all orders with their deadlines
    orders = Order.objects.all().prefetch_related('product')
    order_deadlines = {}
    for order in orders:
        order_deadlines[order.order_number] = order.deadline
        # Check if the order deadline is overdue compared to today
        plate_key = (order.order_number, order.product.name)
        plate_complete_date = plates_complete_dates.get(plate_key)
        order.plate_complete_date = plate_complete_date
        order.is_overdue = ((order.deadline and plate_complete_date)
                            and order.deadline < (plate_complete_date + datetime.timedelta(days=parameters.production_lag)))

    table_data = []
    for i in range(parameters.tracks_count):
        table_data.append([])
        for j, day_roads in enumerate(production_days.values()):
            if i > available_tracks[j].count - 1:
                table_data[i].append(None)
                continue

            if i < len(day_roads):
                production_day = day_roads[i]
                # Check if any plates in this production day have overdue deadlines
                for plate in production_day.plates.all():
                    if plate.order and plate.order in order_deadlines:
                        deadline = order_deadlines[plate.order]
                        if deadline and deadline < (production_day.date + datetime.timedelta(days=parameters.production_lag)):
                            production_day.has_overdue_deadline = True
                            break
                table_data[i].append(production_day)
            else:
                table_data[i].append({
                    'free_len': Parameters.get_solo().road_length,
                })

    today_production_day = list(ProductionDay.objects.filter(date=datetime.date.today()))
    today_max_length = (AvailableTrack.get_tracks(datetime.date.today()).filter(date=datetime.date.today()).first().count
                        * Parameters.get_solo().road_length)
    today_useful = sum([sum([ip.count * ip.length for ip in i.plates.all()])
                        for i in today_production_day]) / today_max_length if today_max_length else 0
    today_stats = {
        'tracks': len(today_production_day),
        'plates': sum([sum([ip.count for ip in i.plates.all()]) for i in today_production_day]),
        'useful': round(today_useful * 100, 2),
    }
    all_max_length = (sum([i.count for i in available_tracks if i.count and len(production_days[i.date]) != 0])
                        * Parameters.get_solo().road_length)

    retool_price = sum([i for i in DailyRetooling.objects.all().values_list('price', flat=True)])
    all_cost = sum(ProductionDay.objects.all().values_list('total_cost', flat=True)) + retool_price
    useful = (sum([sum([ip.count * ip.length for ip in i.plates.all()])
                       for i in ProductionDay.objects.all()]) / all_max_length if all_max_length else 0)
    all_stats = {
        'tracks': len(ProductionDay.objects.all()),
        'plates': sum([sum([ip.count for ip in i.plates.all()]) for i in ProductionDay.objects.all()]),
        'useful': round(useful * 100, 2),
        'retool_count': sum([i for i in DailyRetooling.objects.all().values_list('count', flat=True)]),
        'all_cost': all_cost
    }
    last_complete_date = max(plates_complete_dates.values(), default=None)

    return render(request, 'calculation/index.html', {
        'table_data': table_data,
        'price_table_data': UnitPrice.objects.all(),
        'parameters': parameters,
        'inventory': Inventory.objects.all(),
        'unplaced_plates': UnplacedPlate.objects.all(),
        'used_ready_plates': UsedReadyPlate.objects.all(),
        'orders': sorted(orders,
                         key=lambda x: (not x.is_overdue, x.deadline or datetime.date.max, x.plate_complete_date or datetime.date.max)),
        'available_tracks': available_tracks,
        'today': datetime.date.today(),
        'stats': today_stats,
        'all_stats': all_stats,
        'last_complete_date': last_complete_date,
        'table_height': str(176.648 * parameters.tracks_count + 132.6).replace(',', '.').replace(' ', ''),
    })


def update_available_tracks(tracks, date_from, date_to):
    old_tracks = list(AvailableTrack.get_tracks(date_from, date_to))
    for i, track in enumerate(tracks):
        old_tracks[i].count = track
    AvailableTrack.objects.bulk_update(old_tracks, ['count'])

@logger.catch
@handle_view_exception
@login_required(login_url='/admin/login/')
def fetch_and_save_production_plan(request):
    if request.method == 'POST':
        date_from, date_to = get_date_range_from_request(request)
        date_to = date_from + datetime.timedelta(days=100)
        tracks = list(map(int, request.POST['tracks'].split(',')))
        update_available_tracks(tracks, date_from, date_to)

        with transaction.atomic():
            clear_old_data(date_from)
            update_data()
            calculate_plan(date_from, date_to)
        return redirect('index')
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)


@handle_view_exception
@login_required(login_url='/admin/login/')
def change_available_tracks(request):
    if request.method == 'POST':
        track_day = int(request.POST.get('day'))
        track_count = int(request.POST.get('count'))
        available_tracks = AvailableTrack.objects.order_by('date').all()
        available_track = available_tracks[track_day - 1]
        available_track.count = track_count
        available_track.save()
        print(available_track)
        return JsonResponse({'status': 'success', 'message': 'Track status changed'})
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)


@handle_view_exception
@login_required(login_url='/admin/login/')
def generate_production_calendar(request):
    deadlines = dict(Order.objects.values_list('order_number', 'deadline'))
    date = request.GET.get('date_print', datetime.date.today().strftime("%Y-%m-%d"))
    tracks = ProductionDay.objects.filter(date=date)
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date().strftime("%d.%m.%Y")

    def update_plate_info(plate):
        if plate.order in deadlines and deadlines[plate.order]:
            plate.deadline = deadlines[plate.order].strftime("%d.%m.%Y")
        else:
            plate.deadline = None
        return plate


    # Пример данных для трех дорожек
    data = {
        "date": date,
        "tracks": [
            {
                "name": f"Дорожка №{i}",
                "plates": list(map(update_plate_info, track.plates.all())),
            }
            for i, track in enumerate(tracks, 1)
        ]
    }

    html_string = render_to_string('calculation/production_calendar_template.html', data)
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="production_calendar.pdf"'
    return response
