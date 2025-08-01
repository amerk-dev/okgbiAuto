import datetime

import json
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from loguru import logger
from weasyprint import HTML

from .models import (Order, Parameters, ReadyPlate, Track, UnitPrice, Plate)
from .services.calculator import calculate_plan
from .services.export_1c import export_to_1c
from .services.manage_1c import Update1CDataCommand
from .services.stats import Stats
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


# @handle_view_exception
@login_required(login_url='/admin/login/')
@logger.catch
def index(request):
    parameters = Parameters.get_solo()

    raw_table_data = defaultdict(list)
    for track in Track.objects.all():
        raw_table_data[track.position].append(track)

    for p in raw_table_data:
        while len(raw_table_data[p]) < parameters.tracks_count:
            raw_table_data[p].append(None)

    table_data = [raw_table_data[i] for i in sorted(raw_table_data.keys())]

    print(table_data)

    last_complete_date = ''
    last_complete_track = Track.objects.order_by('-day').first()
    if last_complete_track and last_complete_track.plates.exists():
        last_complete_date = last_complete_track.day

    orders = Order.objects.filter(is_deleted=False)
    # Get deleted orders
    deleted_orders = Order.objects.filter(is_deleted=True)

    return render(request, 'calculation/index.html', {
        'table_data': table_data,
        'price_table_data': UnitPrice.objects.all(),
        'parameters': parameters,
        'unplaced_plates': Plate.objects.filter(track=None),
        'used_ready_plates': ReadyPlate.objects.all(),
        'orders': sorted(orders,
                         key=lambda x: (not x.is_overdue, x.last_deadline.date or datetime.date.max, x.complete_date or datetime.date.max)),
        'deleted_orders': deleted_orders,
        'today': datetime.date.today(),
        'stats': Stats.get_today_stats(),
        'all_stats': Stats.get_all_stats(),
        'last_complete_date': last_complete_date,
        'table_height': str(176.648 * parameters.tracks_count + 132.6).replace(',', '.').replace(' ', ''),
    })



@logger.catch
@handle_view_exception
@login_required(login_url='/admin/login/')
def fetch_and_save_production_plan(request):
    if request.method == 'POST':
        with transaction.atomic():
            Update1CDataCommand().execute()
            calculate_plan()
        return redirect('index')
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)


@handle_view_exception
@login_required(login_url='/admin/login/')
def change_available_tracks(request):
    if request.method == 'POST':
        track_day = int(request.POST.get('day'))
        track_count = int(request.POST.get('count'))
        available_tracks = Track.objects.order_by('date').all()
        available_track = available_tracks[track_day - 1]
        available_track.count = track_count
        available_track.save()
        print(available_track)
        return JsonResponse({'status': 'success', 'message': 'Track status changed'})
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)


@handle_view_exception
@login_required(login_url='/admin/login/')
@require_POST
@handle_view_exception
@login_required(login_url='/admin/login/')
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.is_deleted = True
    order.save()
    return JsonResponse({'status': 'success'})


@require_POST
@handle_view_exception
@login_required(login_url='/admin/login/')
def restore_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.is_deleted = False
    order.save()
    return JsonResponse({'status': 'success'})


@require_POST
@handle_view_exception
@login_required(login_url='/admin/login/')
def delete_plate(request, plate_type, plate_id):
    plate_models = {
        'unplaced': UnplacedPlate,
        'used_ready': UsedReadyPlate,
        'production_day': ProductionDayPlate,
    }

    if plate_type not in plate_models:
        return JsonResponse({'status': 'error', 'message': 'Invalid plate type'}, status=400)

    plate = get_object_or_404(plate_models[plate_type], id=plate_id)
    plate.is_deleted = True
    plate.save()
    return JsonResponse({'status': 'success'})


@require_POST
@handle_view_exception
@login_required(login_url='/admin/login/')
def restore_plate(request, plate_type, plate_id):
    plate_models = {
        'unplaced': UnplacedPlate,
        'used_ready': UsedReadyPlate,
        'production_day': ProductionDayPlate,
    }

    if plate_type not in plate_models:
        return JsonResponse({'status': 'error', 'message': 'Invalid plate type'}, status=400)

    plate = get_object_or_404(plate_models[plate_type], id=plate_id)
    plate.is_deleted = False
    plate.save()
    return JsonResponse({'status': 'success'})


@require_POST
@handle_view_exception
@login_required(login_url='/admin/login/')
def move_plate(request):
    """
    Обработчик для перемещения плиты между дорожками
    """
    try:
        data = json.loads(request.body)
        source_row = data.get('sourceRow')
        source_col = data.get('sourceCol')
        target_row = data.get('targetRow')
        target_col = data.get('targetCol')

        # Получаем даты из доступных дорожек
        available_tracks = list(AvailableTrack.objects.all().order_by('date'))

        # Получаем дату источника и цели
        source_date = available_tracks[source_col].date
        target_date = available_tracks[target_col].date

        # Получаем плиту из исходной дорожки
        source_production_day = ProductionDay.objects.filter(date=source_date).order_by('id')[source_row]

        # Проверяем, существует ли целевая дорожка
        target_production_days = ProductionDay.objects.filter(date=target_date)

        # Если целевая дорожка не существует, создаем её
        if target_row >= len(target_production_days):
            # Создаем новую дорожку с такими же параметрами, как у исходной
            target_production_day = ProductionDay.objects.create(
                date=target_date,
                height=source_production_day.height,
                width=source_production_day.width,
                useful_len=0,
                free_len=Parameters.get_solo().road_length,
                concrete_class=source_production_day.concrete_class,
                wire_bottom=source_production_day.wire_bottom,
                wire_top=source_production_day.wire_top,
                total_cost=0,
                free_cost=0,
                full_cost=0
            )
        else:
            target_production_day = target_production_days[target_row]

        # Перемещаем все плиты из исходной дорожки в целевую
        plates = source_production_day.plates.all()
        for plate in plates:
            plate.production_day = target_production_day
            plate.save()

        # Обновляем полезную длину и свободную длину
        total_length = sum(plate.length * plate.count for plate in plates)
        target_production_day.useful_len = total_length
        target_production_day.free_len = Parameters.get_solo().road_length - total_length
        target_production_day.save()

        # Удаляем исходную дорожку, если она пуста
        source_production_day.delete()

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
@handle_view_exception
@login_required(login_url='/admin/login/')
def export_to_1c_view(request):
    """
    Обработчик для выгрузки данных в 1С
    """
    result = export_to_1c()
    if result['status'] == 'success':
        return JsonResponse({'status': 'success', 'message': result['message']})
    else:
        return JsonResponse({'status': 'error', 'message': result['message']}, status=500)


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


@login_required(login_url='/admin/login/')
@logger.catch
def algorithm(request):
    """
    Render the algorithm explanation page
    """
    return render(request, 'calculation/algorithm.html')


@login_required(login_url='/admin/login/')
@logger.catch
@handle_view_exception
def algorithm_demo(request):
    """
    Handle the algorithm demo form submission
    """
    if request.method == 'POST' and request.FILES.get('demo_file'):
        try:
            demo_file = request.FILES['demo_file']
            file_content = demo_file.read().decode('utf-8')
            data = json.loads(file_content)

            # Process the data (this is a placeholder - actual processing would depend on your algorithm)
            # For demonstration, we'll just return the formatted JSON
            result = json.dumps(data, indent=4)

            return render(request, 'calculation/algorithm.html', {'result': result})
        except Exception as e:
            return render(request, 'calculation/algorithm.html', {'result': f"Error processing file: {str(e)}"})

    return redirect('algorithm')
