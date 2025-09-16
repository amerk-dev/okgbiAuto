import datetime
import tempfile

from django.db.models import Prefetch
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from weasyprint import HTML

from django.db import transaction
from .services.calculator.calculate import calculate_plan
from .services.manage_1c import Update1CDataCommand
from .services.export_1c import export_to_1c
from django.views.generic import TemplateView

from .models import (
    Customer, Deadline, Order, Parameters, ReadyPlate, Track, UnitPrice, Plate,
    UnitTypeChoice
)
from .models.params import HolidayDate
from .services.stats import Stats
from .serializers import (
    CustomerSerializer, TrackSerializer, PlateSerializer, ReadyPlateSerializer,
    OrderSerializer, UnitPriceSerializer, ParametersSerializer, HolidayDateSerializer
)

# ViewSets
class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for customers
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        """Override list method to return just the customer names"""
        customers = self.queryset.values_list('name', flat=True)
        return Response(list(customers))

class TrackViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tracks
    """
    queryset = Track.objects.all().order_by('id')
    serializer_class = TrackSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['get'])
    def slabs(self, request, pk=None):
        """Get slabs for a specific track"""
        track = self.get_object()
        plates = track.plates.all().prefetch_related('deadline', 'deadline__order')

        slabs_data = []
        for plate in plates:
            # Get customer name from the track
            # Get deadline date
            deadline_date = plate.deadline.date.strftime('%d.%m.%Y') if plate.deadline and plate.deadline.date else "Не указан"

            # Get order number
            order_number = plate.deadline.order.order_number if plate.deadline and plate.deadline.order else "Не указан"
            customer_name = plate.deadline.order.customer.name if plate.deadline and plate.deadline.order and plate.deadline.order.customer else "Не указан"

            slabs_data.append({
                'customer': customer_name,
                'deadline_date': deadline_date,
                'order_number': order_number,
                'id': plate.id,
                'name': plate.name,
                'length': plate.length,
                'width': plate.width,
                'height': plate.height,
                'load': plate.capacity,
                'concrete_class': plate.concrete_class,
                'wire_top': int(plate.wire_top),
                'wire_bottom': int(plate.wire_bottom)
            })

        return Response(slabs_data)


    def list(self, request):
        """Optimized list method to return tracks with slabs"""

        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        # Берём все треки с нужными связями
        tracks = (
            Track.objects
            .select_related("customer")
            .prefetch_related(
                Prefetch("plates", queryset=Plate.objects.all().select_related("deadline__order"))
            )
            .order_by("position", "day")
        )

        # Группируем по position
        positions = {}
        for track in tracks:
            if track.position not in positions:
                positions[track.position] = []
            positions[track.position].append(track)

        result = []

        for pos, pos_tracks in positions.items():
            first_track = pos_tracks[0]

            track_data = {
                "id": first_track.id,
                "name": f"Дорожка {pos + 1}",
                "contractor": first_track.customer.name if first_track.customer else "",
                "days": [],
            }

            # Группировка по дате
            days = {}
            for t in pos_tracks:
                if t.day not in days:
                    days[t.day] = []
                days[t.day].append(t)

            for date, day_tracks in days.items():
                day_track = day_tracks[0]  # берём первый (или можно объединять данные)

                # Формат даты
                if date == today:
                    display_date = "today"
                elif date == tomorrow:
                    display_date = "tomorrow"
                else:
                    display_date = date.strftime("%Y-%m-%d")

                # KPI
                # day_kpi = Stats.calculate_day_kpi(date)
                kpi_score = 0

                # Сумма overendering_wire_kg по всем трекам за этот день
                total_overendering_wire_kg = sum(
                    t.overendering_wire_kg for t in Track.objects.filter(day=date) if t.plates.exists()
                )

                day_data = {
                    "date": display_date,
                    "slabs": [],
                    "freeSpace": f"{day_track.free_length}мм",
                    "kpi": kpi_score,
                    "total_overendering_wire_kg": total_overendering_wire_kg,
                }

                if day_track.plates.exists():
                    price_str = f"{day_track.cost:.2f}".replace(".", ",")
                    track_orders = [
                        plate.deadline.order.order_number
                        for plate in day_track.plates.all()
                        if plate.deadline and plate.deadline.order
                    ]
                    track_plates_names = [plate.name for plate in day_track.plates.all()]

                    info = {
                        "id": str(day_track.id),
                        "number": f"#{day_track.id}",
                        "orders": track_orders,
                        "plates": track_plates_names,
                        "size": f"{int(day_track.width)}x{int(day_track.height)}",
                        "width": int(day_track.width),
                        "height": int(day_track.height),
                        "wireTop": day_track.wire_top,
                        "wireBottom": day_track.wire_bottom,
                        "concrete": day_track.concrete_class,
                        "occupied": day_track.useful_length,
                        "free": day_track.free_length,
                        "price": f"{price_str} ₽",
                        "deadline": (
                            day_track.deadline.strftime("%d-%m-%Y")
                            if day_track.deadline
                            else None
                        ),
                        "status": "overdue" if day_track.has_overdue_deadline else "booked",
                        "is_manual": day_track.is_manual,
                        "overendering_wire_kg": day_track.overendering_wire_kg,
                    }
                    day_data.update(info)
                else:
                    day_data.update(
                        {
                            "id": str(day_track.id),
                            "free": str(day_track.free_length),
                        }
                    )

                track_data["days"].append(day_data)

            result.append(track_data)

        return Response(result)


    @action(detail=True, methods=['post'])
    def update_contractor(self, request, pk=None):
        """Update track contractor for all tracks with the same position"""
        track = self.get_object()
        contractor_name = request.data.get('contractor')

        # Get all tracks with the same position
        tracks_with_same_position = Track.objects.filter(position=track.position)

        if contractor_name:
            # Get or create contractor
            contractor, created = Customer.objects.get_or_create(name=contractor_name)
            # Update all tracks with the same position
            tracks_with_same_position.update(customer=contractor)
        else:
            # Set customer to None for all tracks with the same position
            tracks_with_same_position.update(customer=None)

        return Response({'status': 'success'})

    @action(detail=False, methods=['post'])
    def swap(self, request, pk=None):
         if 'track1Id' in request.data and 'track2Id' in request.data:
            # Swap tracks (position and day)
            track1_id = request.data.get('track1Id')
            track2_id = request.data.get('track2Id')

            track1 = Track.objects.get(id=track1_id)
            track2 = Track.objects.get(id=track2_id)

            # Swap position and day
            track1_position = track1.position
            track1_day = track1.day

            track1.position = track2.position
            track1.day = track2.day
            track1.is_manual = True

            track2.position = track1_position
            track2.day = track1_day
            track2.is_manual = True

            track1.save()
            track2.save()

            return Response({'status': 'success'})
         raise ValidationError('Invalid request')

    @action(detail=False, methods=['post'], url_path='transfer-slabs')
    def transfer_slabs(self, request):
        """Transfer multiple slabs to another track on a specific date"""
        if 'slabIds' in request.data and 'targetTrackPosition' in request.data and 'targetDate' in request.data:
            slab_ids = request.data.get('slabIds')
            target_track_position = int(request.data.get('targetTrackPosition').split(' ')[1]) - 1
            target_date = request.data.get('targetDate')

            # Convert target_date to datetime.date if it's a string
            if isinstance(target_date, str):
                try:
                    target_date = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
                except ValueError:
                    raise ValidationError('Invalid date format. Expected YYYY-MM-DD')

            # Get the target track
            try:
                target_track = Track.objects.get(position=target_track_position, day=target_date)
            except Track.DoesNotExist:
                # Create a new track if it doesn't exist
                params = Parameters.get_solo()
                # Use the provided position
                position = int(target_track_position)
                if position >= params.default_available_tracks:
                    raise ValidationError(f'Максимальное количество треков ({params.default_available_tracks}) для этой даты уже достигнутo')

                target_track = Track.objects.create(
                    position=position,
                    day=target_date
                )

            # Get the slabs to transfer
            slabs = Plate.objects.filter(id__in=slab_ids, is_deleted=False)
            if not slabs:
                raise ValidationError('No slabs found with the provided IDs')

            # Check if the target track already has slabs
            if target_track.plates.exists():
                # Check if the width and height of the target track match the slabs
                target_width = target_track.width
                target_height = target_track.height

                for slab in slabs:
                    if slab.width != target_width or slab.height != target_height:
                        raise ValidationError(
                            f'Размеры плиты (ширина: {slab.width}, высота: {slab.height}) не совпадает. '
                            f'Размеры целевого трека (ширина: {target_width}, высота: {target_height})'
                        )

            # Check if the track's length won't be exceeded
            params = Parameters.get_solo()
            current_length = target_track.useful_length
            additional_length = sum(slab.length for slab in slabs)

            if current_length + additional_length > params.road_length:
                raise ValidationError(
                    f'Track length would be exceeded. Current: {current_length}, '
                    f'Additional: {additional_length}, Maximum: {params.road_length}'
                )

            # Store the source tracks before transferring
            source_tracks = set()
            for slab in slabs:
                if slab.track:
                    source_tracks.add(slab.track)

                # Transfer the slab
                slab.track = target_track
                slab.save()

            # Refresh the source tracks' data
            for source_track in source_tracks:
                source_track.refresh_from_db()

            # Refresh the target track's data
            target_track.refresh_from_db()

            return Response({'status': 'success'})

        raise ValidationError('Invalid request. Required parameters: slabIds, targetTrackPosition, targetDate')

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for orders
    """
    queryset = Order.objects.all().order_by('-id')
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        """Override list method to return orders in the format expected by the frontend"""
        orders = self.get_queryset()
        orders_data = []
        for order in orders:
            for plate in Plate.objects.filter(deadline__order=order, is_deleted=False):
                if not any(data['number'] == order.order_number and data['raw_name'] == plate.name for data in orders_data):
                    orders_data.append({
                        'id': order.id,
                        'customer': order.customer.name if order.customer else None,
                        'number': order.order_number,
                        'deadline': order.last_deadline.date.strftime('%d.%m.%Y') if order.last_deadline.date else None,
                        'completeDate': order.complete_date.strftime('%d.%m.%Y') if order.complete_date else None,
                        'is_deleted': order.is_deleted,
                        'raw_name': plate.name,
                        'name': plate.clean_name,
                        'capacity': plate.capacity,
                        'concrete': plate.concrete_class,
                        'height': plate.height,
                        'width': plate.width,
                        'length': plate.length,
                        'wireTop': int(plate.wire_top),
                        'wireBottom': int(plate.wire_bottom),
                        'status': plate.is_overdue,
                        'slabCount': 1
                    })
                else:
                    for data in orders_data:
                        if data['number'] == order.order_number and data['raw_name'] == plate.name:
                            data['slabCount'] += 1
                            data['status'] = data['status'] or plate.is_overdue
                            break

        return Response(orders_data)

    @action(detail=False, methods=['get'])
    def deleted(self, request):
        """Return deleted orders"""
        orders = self.queryset
        orders_data = []
        for order in orders:
            for plate in Plate.all_objects.filter(deadline__order=order, is_deleted=True):
                if not any(data['number'] == order.order_number and data['raw_name'] == plate.name for data in orders_data):
                    orders_data.append({
                        'id': order.id,
                        'customer': order.customer.name if order.customer else None,
                        'number': order.order_number,
                        'deadline': order.last_deadline.date.strftime('%d.%m.%Y') if order.last_deadline.date else None,
                        'completeDate': order.complete_date.strftime('%d.%m.%Y') if order.complete_date else None,
                        'is_deleted': order.is_deleted,
                        'raw_name': plate.name,
                        'name': plate.clean_name,
                        'capacity': plate.capacity,
                        'concrete': plate.concrete_class,
                        'height': plate.height,
                        'width': plate.width,
                        'length': plate.length,
                        'wireTop': int(plate.wire_top),
                        'wireBottom': int(plate.wire_bottom),
                        'status': plate.is_overdue,
                        'slabCount': 1
                    })
                else:
                    for data in orders_data:
                        if data['number'] == order.order_number and data['raw_name'] == plate.name:
                            data['slabCount'] += 1
                            data['status'] = data['status'] or plate.is_overdue
                            break

        return Response(orders_data)

    def destroy(self, request, *args, **kwargs):
        """Mark order as deleted instead of actually deleting it"""
        order = self.get_object()
        plate_name = request.data.get('plateName')
        Plate.objects.filter(deadline__order=order, name=plate_name).update(is_deleted=True)
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def restore(self, request, *args, **kwargs):
        """Restore a deleted order by marking its plates as not deleted"""
        order = self.get_object()
        plate_name = request.data.get('plateName')
        Plate.all_objects.filter(deadline__order=order, name=plate_name, is_deleted=True).update(is_deleted=False)
        return Response({'status': 'success'})

class PlateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for plates
    """
    queryset = Plate.objects.all()
    serializer_class = PlateSerializer
    permission_classes = [permissions.AllowAny]

    def update(self, request, *args, **kwargs):
        """Update a plate"""
        plate = self.get_object()

        # Store the original track for later reference
        original_track = plate.track

        # Get the data from the request
        name = request.data.get('name', plate.name)
        length = request.data.get('length', plate.length)
        concrete_class = request.data.get('concrete_class', plate.concrete_class)
        wire_top = request.data.get('wire_top', plate.wire_top)
        wire_bottom = request.data.get('wire_bottom', plate.wire_bottom)

        # Update the plate
        plate.name = name
        plate.length = length
        plate.concrete_class = concrete_class
        plate.wire_top = wire_top
        plate.wire_bottom = wire_bottom

        # Save the plate
        plate.save()

        # Refresh the track data if the plate is assigned to a track
        if original_track:
            # The track properties are calculated dynamically based on its plates,
            # so we just need to ensure the track object is refreshed from the database
            original_track.refresh_from_db()

        # Return the updated plate
        serializer = self.get_serializer(plate)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Mark plate as deleted instead of actually deleting it"""
        plate = self.get_object()

        # Store the track reference
        track = plate.track

        # Mark the plate as deleted
        plate.is_deleted = True
        plate.save()

        # Refresh the track data if the plate was assigned to a track
        if track:
            # The track properties are calculated dynamically based on its plates,
            # so we just need to ensure the track object is refreshed from the database
            track.refresh_from_db()

        return Response({'status': 'success'})

class ReadyPlateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ready plates
    """
    queryset = ReadyPlate.objects.all()
    serializer_class = ReadyPlateSerializer
    permission_classes = [permissions.AllowAny]

class UnitPriceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for unit prices
    """
    queryset = UnitPrice.objects.all()
    serializer_class = UnitPriceSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def materials(self, request):
        """Get all materials"""
        materials = []

        # Get concrete prices
        concrete_prices = UnitPrice.objects.filter(unit=UnitTypeChoice.PLATE)
        concrete_serializer = UnitPriceSerializer(concrete_prices, many=True)

        for unit_price_data in concrete_serializer.data:
            materials.append({
                'id': unit_price_data['id'],
                'name': f'Бетон {unit_price_data.get("concrete_class", "")}',
                'unit': 'м³',
                'price': float(unit_price_data.get('price', 0))
            })

        # Get wire price
        wire_price = UnitPrice.objects.get(unit=UnitTypeChoice.WIRE)
        wire_serializer = UnitPriceSerializer(wire_price)
        wire_data = wire_serializer.data

        materials.append({
            'id': wire_data['id'],
            'name': wire_data.get('name', 'Проволока'),
            'unit': 'кг',
            'price': float(wire_data.get('price', 0))
        })

        return Response(materials)

    @action(detail=False, methods=['post'])
    def update_materials(self, request):
        """Update material prices"""
        materials = request.data.get('materials', [])

        for material in materials:
            unit_price = UnitPrice.objects.get(id=material['id'])
            unit_price.price = material['price']
            unit_price.save()

        return Response({'status': 'success'})

class ParametersViewSet(viewsets.ModelViewSet):
    """
    API endpoint for parameters
    """
    queryset = Parameters.objects.all()
    serializer_class = ParametersSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def track_settings(self, request):
        """Get track settings"""
        # Get parameters
        params = Parameters.get_solo()
        params_serializer = ParametersSerializer(params)
        params_data = params_serializer.data

        # Get retooling price
        retooling_price = UnitPrice.objects.get(unit=UnitTypeChoice.RETOOLING)
        retooling_serializer = UnitPriceSerializer(retooling_price)
        retooling_data = retooling_serializer.data

        # Get holiday dates
        holiday_dates = HolidayDate.objects.all()
        holiday_dates_serializer = HolidayDateSerializer(holiday_dates, many=True)
        holiday_dates_data = holiday_dates_serializer.data

        # Map weekend days to frontend format
        weekend_days = []
        if params_data.get('monday_weekend'):
            weekend_days.append('Понедельник')
        if params_data.get('tuesday_weekend'):
            weekend_days.append('Вторник')
        if params_data.get('wednesday_weekend'):
            weekend_days.append('Среда')
        if params_data.get('thursday_weekend'):
            weekend_days.append('Четверг')
        if params_data.get('friday_weekend'):
            weekend_days.append('Пятница')
        if params_data.get('saturday_weekend'):
            weekend_days.append('Суббота')
        if params_data.get('sunday_weekend'):
            weekend_days.append('Воскресенье')

        # Format data for frontend
        track_settings = {
            'reconfigurationCost': float(retooling_data.get('price', 0)),
            'trackLength': params_data.get('road_length', 0),
            'trackCount': params_data.get('tracks_count', 0),
            'tracksInWork': params_data.get('tracks_count', 0),  # Default to all tracks
            'tailLength': params_data.get('tail_length', 0),
            'weekendDays': weekend_days,
            'holidayDates': [item['date'] for item in holiday_dates_data]
        }

        return Response(track_settings)

    @action(detail=False, methods=['post'])
    def update_track_settings(self, request):
        """Update track settings"""
        # Update retooling cost
        retooling_price = UnitPrice.objects.get(unit=UnitTypeChoice.RETOOLING)
        retooling_price.price = request.data.get('reconfigurationCost', retooling_price.price)
        retooling_price.save()

        # Update track settings
        params = Parameters.get_solo()
        params.road_length = request.data.get('trackLength', params.road_length)
        params.tracks_count = request.data.get('trackCount', params.tracks_count)
        params.tail_length = request.data.get('tailLength', params.tail_length)

        # Update weekend days
        weekend_days = request.data.get('weekendDays', [])
        params.monday_weekend = 'Понедельник' in weekend_days
        params.tuesday_weekend = 'Вторник' in weekend_days
        params.wednesday_weekend = 'Среда' in weekend_days
        params.thursday_weekend = 'Четверг' in weekend_days
        params.friday_weekend = 'Пятница' in weekend_days
        params.saturday_weekend = 'Суббота' in weekend_days
        params.sunday_weekend = 'Воскресенье' in weekend_days

        params.save()

        # Update holiday dates
        holiday_dates = request.data.get('holidayDates', [])

        # Clear existing holiday dates and create new ones
        HolidayDate.objects.all().delete()

        for date_str in holiday_dates:
            HolidayDate.objects.create(date=date_str)

        return Response({'status': 'success'})


class StockView(APIView):
    """
    API endpoint for stock data
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Get stock data (used, available, unplaced)"""
        # Get used stock (plates assigned to orders)
        plates = ReadyPlate.objects.all()
        used_stock = []

        for plate in plates:
            used_stock.append({
                'id': plate.id,
                'name': plate.clean_name,
                'length': plate.length,
                'width': plate.width,
                'height': plate.height,
                'capacity': f"{plate.capacity} кг/м²",
                'concrete': plate.concrete_class,
                'wireTop': plate.wire_top,
                'wireBottom': plate.wire_bottom,
                'count': 1,
                'order': f"#{plate.used_in_order.order_number}" if plate.used_in_order else None,
            })

        return Response(used_stock)

class DashboardStatsView(APIView):
    """
    API endpoint for dashboard statistics
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Get dashboard statistics"""
        stats = Stats()

        # Get today's stats
        today_stats = stats.get_today_stats()

        # Get overall stats
        overall_stats = stats.get_all_stats()

        dashboard_stats = [
            {
                'id': 1,
                'section': 'Статистика на сегодня',
                'title': 'Занято дорожек',
                'value': f"{today_stats['tracks']} шт",
                'icon': 'road',
                'color': 'blue'
            },
            {
                'id': 2,
                'section': 'Статистика на сегодня',
                'title': 'Изготовления',
                'value': f"{today_stats['plates']} плит",
                'icon': 'cube',
                'color': 'green'
            },
            {
                'id': 3,
                'section': 'Статистика на сегодня',
                'title': 'Занято',
                'value': f"{today_stats['useful']:.1f} %",
                'icon': 'percentage',
                'color': 'yellow'
            },
            {
                'id': 4,
                'section': 'Общая статистика',
                'title': 'Занято дорожек',
                'value': f"{overall_stats['tracks']} шт",
                'icon': 'road',
                'color': 'blue'
            },
            {
                'id': 5,
                'section': 'Общая статистика',
                'title': 'Изготовления',
                'value': f"{overall_stats['plates']} плит",
                'icon': 'cube',
                'color': 'green'
            },
            {
                'id': 6,
                'section': 'Общая статистика',
                'title': 'Занято',
                'value': f"{overall_stats['useful']:.2f} %",
                'icon': 'percentage',
                'color': 'yellow'
            },
            {
                'id': 7,
                'section': 'Общая статистика',
                'title': 'Количество переналадок',
                'value': f"{overall_stats['retool_count']} шт",
                'icon': 'wrench',
                'color': 'purple'
            },
            {
                'id': 8,
                'section': 'Общая статистика',
                'title': 'Стоимость',
                'value': f"{overall_stats['all_cost']:.2f} р",
                'icon': 'money-bill-wave',
                'color': 'green'
            },
            {
                'id': 9,
                'section': 'Общая статистика',
                'title': 'Дата готовности',
                'value': overall_stats['last_track'],
                'icon': 'calendar-check',
                'color': 'blue'
            },
            # KPI metrics
            {
                'id': 10,
                'section': 'KPI расстановки плит',
                'title': 'Общий KPI',
                'value': f"{overall_stats['kpi_score']:.2f}",
                'icon': 'line-chart',
                'color': 'blue',
                'tooltip': 'Чем ниже значение, тем лучше расстановка'
            },
            {
                'id': 11,
                'section': 'KPI расстановки плит',
                'title': 'Перерасход на типе бетона',
                'value': f"{overall_stats['kpi_concrete_economy']:.2f} ₽",
                'icon': 'cubes',
                'color': 'green',
                'tooltip': 'Штраф за избыточное использование дорогих марок бетона'
            },
            {
                'id': 12,
                'section': 'KPI расстановки плит',
                'title': 'Перерасход проволоки',
                'value': f"{overall_stats['kpi_wire_economy']:.2f} ₽ ",
                'icon': 'cog',
                'color': 'yellow',
                'tooltip': 'Штраф за перерасход армирования'
            },
            {
                'id': 13,
                'section': 'KPI расстановки плит',
                'title': 'Соблюдение дедлайнов',
                'value': f"{overall_stats['kpi_deadline_compliance']:.2f}",
                'icon': 'calendar-times',
                'color': 'red',
                'tooltip': 'Штраф за просрочку выполнения заказов'
            },
            {
                'id': 14,
                'section': 'KPI расстановки плит',
                'title': 'Загрузка дорожек',
                'value': f"{overall_stats['kpi_track_loading']:.2f} %",
                'icon': 'percentage',
                'color': 'purple',
                'tooltip': 'Процент неиспользованной мощности дорожек'
            },
            {
                'id': 15,
                'section': 'KPI расстановки плит',
                'title': 'Переналадки оборудования',
                'value': f"{overall_stats['kpi_retooling_efficiency']:.2f}",
                'icon': 'cogs',
                'color': 'orange',
                'tooltip': 'Среднее количество переналадок на одну дорожку'
            }
        ]

        return Response(dashboard_stats)


class CalculationView(APIView):
    """
    API endpoint for starting a calculation
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Start a calculation"""
        with transaction.atomic():
            Update1CDataCommand().execute()

            calculate_plan()
        return Response({'status': 'success', 'message': 'Calculation successfully'})


class PrintTrackPlanView(APIView):
    """
    API endpoint for printing track plans
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        date_str = request.query_params.get('date')
        track_id = request.query_params.get('track_id')

        try:
            # Parse the date string to a datetime object
            if date_str:
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date = datetime.date.today()

            # Get tracks for the specified date
            if track_id:
                # Get a specific track
                tracks = Track.objects.filter(id=track_id)
            else:
                # Get all tracks
                tracks = Track.objects.filter(day=date).order_by('position')

            # Prepare data for the template
            tracks_data = []
            for track in tracks:
                # Get plates for this track on the specified date
                plates = track.plates.all()
                if not plates:
                    continue

                # Prepare plate data
                plates_data = []
                for plate in plates:
                    customer = plate.deadline.order.customer.name if plate.deadline.order.customer else None
                    plate_data = {
                        'deadline': plate.deadline.date.strftime('%d.%m.%Y') if plate.deadline and plate.deadline.date else None,
                        'order': plate.deadline.order.order_number if plate.deadline else None,
                        'clean_name': plate.clean_name,
                        'length': plate.length,
                        'width': track.width,
                        'height': track.height,
                        'capacity': plate.capacity,
                        'concrete_class': plate.concrete_class,
                        'wire_top': plate.wire_top,
                        'wire_bottom': plate.wire_bottom,
                        'customer': customer,
                    }
                    plates_data.append(plate_data)

                # Add track data
                track_data = {
                    'name': f"Дорожка {track.position + 1}",
                    'plates': plates_data
                }
                tracks_data.append(track_data)

            # Format the date for display
            if track_id:
                formatted_date = tracks[0].day.strftime('%d.%m.%Y')
            else:
                formatted_date = date.strftime('%d.%m.%Y')

            # Render the HTML template to a string
            html_string = render_to_string('calculation/production_calendar_template.html', {
                'date': formatted_date,
                'tracks': tracks_data
            })

            # Generate PDF from HTML
            pdf_file = HTML(string=html_string).write_pdf()

            # Create HTTP response with PDF content
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'filename="track_plan_{date_str or datetime.date.today()}.pdf"'

            return response

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class Export1CView(APIView):
    """
    API endpoint for exporting data to 1C
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Export data to 1C"""
        try:
            result = export_to_1c()
            return Response(result)
        except Exception as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AlgorithmView(TemplateView):
    """
    View for displaying the algorithm description and demonstration
    """
    template_name = 'calculation/algorithm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AlgorithmDemoView(APIView):
    """
    API endpoint for demonstrating the algorithm with uploaded data
    """
    def post(self, request):
        """Process uploaded file and demonstrate algorithm"""
        if 'demo_file' not in request.FILES:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        demo_file = request.FILES['demo_file']
        try:
            import json
            import tempfile
            from django.db import transaction
            from .services.calculator.calculate import calculate_plan

            # Parse the uploaded JSON file
            file_content = demo_file.read().decode('utf-8')
            data = json.loads(file_content)

            # Start a transaction to create a temporary database state
            with transaction.atomic():
                # Create a savepoint to be able to rollback
                sid = transaction.savepoint()

                # Copy parameters and unit prices from the main database
                params = Parameters.get_solo()
                unit_prices = UnitPrice.objects.all()

                # Process the data and create necessary objects
                # Create customers, orders, deadlines, and plates
                customers = {}
                for order_data in data.get('orders', []):
                    # Create or get customer
                    customer_name = order_data.get('customer', 'Unknown')
                    if customer_name not in customers:
                        customer, _ = Customer.objects.get_or_create(name=customer_name)
                        customers[customer_name] = customer
                    else:
                        customer = customers[customer_name]

                    # Create order
                    order = Order.objects.create(
                        customer=customer,
                        order_number=order_data.get('number', 'Unknown')
                    )

                    # Process completion dates
                    for completion_date in order_data.get('completion_dates', []):
                        date_str = completion_date.get('date')
                        if date_str:
                            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S').date()
                            deadline = Deadline.objects.create(
                                order=order,
                                date=date_obj
                            )

                            # Process plates
                            for plate_data in completion_date.get('plates', []):
                                for _ in range(plate_data.get('count', 1)):
                                    Plate.objects.create(
                                        name=plate_data.get('name', 'Unknown'),
                                        length=plate_data.get('length', 0),
                                        width=plate_data.get('width', 0),
                                        height=plate_data.get('height', 0),
                                        concrete_class=plate_data.get('class', 'B25'),
                                        wire_bottom=plate_data.get('wire_bottom', 0),
                                        wire_top=plate_data.get('wire_top', 0),
                                        deadline=deadline
                                    )

                # Process ready plates
                for ready_plate_data in data.get('ready_plates', []):
                    ReadyPlate.objects.create(
                        name=ready_plate_data.get('name', 'Unknown'),
                        length=ready_plate_data.get('length', 0),
                        width=ready_plate_data.get('width', 0),
                        height=ready_plate_data.get('height', 0),
                        concrete_class=ready_plate_data.get('class', 'B25'),
                        wire_bottom=ready_plate_data.get('wire_bottom', 0),
                        wire_top=ready_plate_data.get('wire_top', 0)
                    )

                # Run the calculation
                calculate_plan()

                # Get the results in a format similar to the main frontend
                tracks = Track.objects.all().order_by('position', 'day')

                # Group tracks by position
                positions = {}
                for track in tracks:
                    if track.position not in positions:
                        positions[track.position] = []
                    positions[track.position].append(track)

                result = []

                for pos, pos_tracks in positions.items():
                    first_track = pos_tracks[0]

                    track_data = {
                        "id": first_track.id,
                        "name": f"Дорожка {pos + 1}",
                        "contractor": first_track.customer.name if first_track.customer else "",
                        "days": [],
                    }

                    # Group by date
                    days = {}
                    for t in pos_tracks:
                        if t.day not in days:
                            days[t.day] = []
                        days[t.day].append(t)

                    for date, day_tracks in days.items():
                        day_track = day_tracks[0]

                        day_data = {
                            "date": date.strftime("%Y-%m-%d"),
                            "slabs": [],
                            "freeSpace": f"{day_track.free_length}мм",
                        }

                        if day_track.plates.exists():
                            price_str = f"{day_track.cost:.2f}".replace(".", ",")
                            track_orders = [
                                plate.deadline.order.order_number
                                for plate in day_track.plates.all()
                                if plate.deadline and plate.deadline.order
                            ]
                            track_plates_names = [plate.name for plate in day_track.plates.all()]

                            info = {
                                "id": str(day_track.id),
                                "number": f"#{day_track.id}",
                                "orders": track_orders,
                                "plates": track_plates_names,
                                "size": f"{int(day_track.width)}x{int(day_track.height)}",
                                "width": int(day_track.width),
                                "height": int(day_track.height),
                                "wireTop": day_track.wire_top,
                                "wireBottom": day_track.wire_bottom,
                                "concrete": day_track.concrete_class,
                                "occupied": day_track.useful_length,
                                "free": day_track.free_length,
                                "price": f"{price_str} ₽",
                                "deadline": (
                                    day_track.deadline.strftime("%d-%m-%Y")
                                    if day_track.deadline
                                    else None
                                ),
                                "status": "overdue" if day_track.has_overdue_deadline else "booked",
                            }
                            day_data.update(info)

                            # Add slabs data
                            for plate in day_track.plates.all():
                                customer_name = plate.deadline.order.customer.name if plate.deadline.order.customer else "Не указан"
                                deadline_date = plate.deadline.date.strftime('%d.%m.%Y') if plate.deadline and plate.deadline.date else "Не указан"
                                order_number = plate.deadline.order.order_number if plate.deadline and plate.deadline.order else "Не указан"

                                day_data["slabs"].append({
                                    'customer': customer_name,
                                    'deadline_date': deadline_date,
                                    'order_number': order_number,
                                    'id': plate.id,
                                    'name': plate.name,
                                    'length': plate.length,
                                    'width': plate.width,
                                    'height': plate.height,
                                    'load': plate.capacity,
                                    'concrete_class': plate.concrete_class,
                                    'wire_top': int(plate.wire_top),
                                    'wire_bottom': int(plate.wire_bottom)
                                })
                        else:
                            day_data.update({
                                "id": str(day_track.id),
                                "free": str(day_track.free_length),
                            })

                        track_data["days"].append(day_data)

                    result.append(track_data)

                # Rollback to the savepoint to clean up
                transaction.savepoint_rollback(sid)

            return Response({'result': result})
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
