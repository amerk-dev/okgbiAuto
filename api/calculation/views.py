import datetime

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from django.db import transaction
from .services.calculator.calculate import claster_plan
from .services.manage_1c import Update1CDataCommand

from .models import (
    Customer, Order, Parameters, ReadyPlate, Track, UnitPrice, Plate,
    UnitTypeChoice
)
from .services.stats import Stats
from .serializers import (
    CustomerSerializer, TrackSerializer, PlateSerializer, ReadyPlateSerializer,
    OrderSerializer, UnitPriceSerializer, ParametersSerializer
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
        plates = track.plates.all()

        slabs_data = []
        for plate in plates:
            # Get customer name from the track
            customer_name = track.customer.name if track.customer else "Не указан"

            # Get deadline date
            deadline_date = plate.deadline.date.strftime('%d.%m.%Y') if plate.deadline and plate.deadline.date else "Не указан"

            # Get order number
            order_number = plate.deadline.order.order_number if plate.deadline and plate.deadline.order else "Не указан"

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
                'wire_top': plate.wire_top,
                'wire_bottom': plate.wire_bottom
            })

        return Response(slabs_data)

    def list(self, request):
        """Override list method to return tracks with slabs"""
        # Get all unique positions
        positions = Track.objects.values_list('position', flat=True).distinct().order_by('position')

        # Format data for frontend
        result = []
        for position in positions:
            # Get the first track with this position
            track = Track.objects.filter(position=position).first()

            track_data = {
                'id': track.id,
                'name': f'Дорожка {track.position + 1}',
                'contractor': track.customer.name if track.customer else '',
                'days': []
            }

            # Get all dates for this track
            dates = Track.objects.filter(position=track.position).values_list('day', flat=True).distinct().order_by('day')

            # Add data for each date
            for date in dates:
                day_track = Track.objects.filter(position=track.position, day=date).prefetch_related('plates', 'plates__deadline__order').first()

                if day_track:
                    # Format date for display
                    if date == datetime.date.today():
                        display_date = 'today'
                    elif date == datetime.date.today() + datetime.timedelta(days=1):
                        display_date = 'tomorrow'
                    else:
                        display_date = date.strftime('%Y-%m-%d')

                    # Calculate KPI for this day
                    day_kpi = Stats.calculate_day_kpi(date)
                    kpi_score = round(day_kpi['score'], 2)

                    # Calculate sum of overendering_wire_kg for this day
                    day_tracks = Track.objects.filter(day=date).prefetch_related('plates')
                    total_overendering_wire_kg = sum(track.overendering_wire_kg for track in day_tracks if track.plates.exists())

                    # Create day data
                    day_data = {
                        'date': display_date,
                        'slabs': [],
                        'freeSpace': f"{day_track.free_length}мм",
                        'kpi': kpi_score,
                        'total_overendering_wire_kg': total_overendering_wire_kg
                    }

                    # Instead of individual slabs, add track info
                    if day_track.plates.exists():
                        # Format price with comma as decimal separator
                        price_str = f"{day_track.cost:.2f}".replace('.', ',')
                        track_orders = [plate.deadline.order.order_number for plate in day_track.plates.all() if plate.deadline and plate.deadline.order]
                        track_plates_names = [plate.name for plate in day_track.plates.all()]
                        info = {
                            'id': f'{day_track.id}',
                            'number': f'#{day_track.id}',
                            'orders': track_orders,
                            'plates': track_plates_names,
                            'size': f'{int(day_track.width)}x{int(day_track.height)}',
                            'width': int(day_track.width),
                            'height': int(day_track.height),
                            'wireTop': f'{day_track.wire_top}',
                            'wireBottom': f'{day_track.wire_bottom}',
                            'concrete': day_track.concrete_class,
                            'occupied': f'{day_track.useful_length}',
                            'free': f'{day_track.free_length}',
                            'price': f'{price_str} ₽',
                            'deadline': day_track.deadline.strftime('%d-%m-%Y') if day_track.deadline else None,
                            'status': 'overdue' if day_track.has_overdue_deadline else 'booked',
                            'is_manual': day_track.is_manual,
                            'overendering_wire_kg': day_track.overendering_wire_kg,
                        }
                        day_data.update(info)
                    else:
                        info = {
                            'id': f'{day_track.id}',
                            'free': f'{day_track.free_length}',
                        }
                        day_data.update(info)

                    track_data['days'].append(day_data)

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
            slabs = Plate.objects.filter(id__in=slab_ids)
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
        orders = self.queryset
        serializer = self.get_serializer(orders, many=True)
        orders_data = serializer.data

        # Format data for frontend
        for order_data in orders_data:
            # Rename fields to match frontend expectations
            order_data['completeDate'] = order_data.pop('complete_date', '')
            order_data['wireTop'] = order_data.pop('wire_top', 0)
            order_data['wireBottom'] = order_data.pop('wire_bottom', 0)
            order_data['slabCount'] = order_data.pop('slab_count', 0)
            order_data['statusClass'] = order_data.pop('status_class', '')

        return Response(orders_data)

    def destroy(self, request, *args, **kwargs):
        """Mark order as deleted instead of actually deleting it"""
        order = self.get_object()
        order.is_deleted = True
        order.save()
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
        """Delete a plate"""
        plate = self.get_object()

        # Store the track reference before deleting the plate
        track = plate.track

        # Delete the plate
        plate.delete()

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

        # Format data for frontend
        track_settings = {
            'reconfigurationCost': float(retooling_data.get('price', 0)),
            'trackLength': params_data.get('road_length', 0),
            'trackCount': params_data.get('tracks_count', 0)
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
        params.save()

        return Response({'status': 'success'})


class StockView(APIView):
    """
    API endpoint for stock data
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Get stock data (used, available, unplaced)"""
        # Get used stock (plates assigned to orders)
        used_plates = Plate.objects.filter(order__isnull=False, track__isnull=False)
        used_serializer = PlateSerializer(used_plates, many=True)
        used_stock = []

        for plate_data in used_serializer.data:
            used_stock.append({
                'id': plate_data['id'],
                'name': plate_data.get('name', ''),
                'length': plate_data.get('length', 0),
                'width': plate_data.get('width', 0),
                'height': plate_data.get('height', 0),
                'capacity': f"{plate_data.get('capacity', 0)} кг/м²",
                'concrete': plate_data.get('concrete_class', ''),
                'wireTop': plate_data.get('wire_top', 0),
                'wireBottom': plate_data.get('wire_bottom', 0),
                'count': 1,
                'order': plate_data.get('order', None)
            })

        # Get available stock (ready plates not assigned to orders)
        ready_plates = ReadyPlate.objects.all()
        ready_serializer = ReadyPlateSerializer(ready_plates, many=True)
        available_stock = []

        for plate_data in ready_serializer.data:
            available_stock.append({
                'id': plate_data['id'],
                'name': plate_data.get('name', ''),
                'length': plate_data.get('length', 0),
                'width': plate_data.get('width', 0),
                'height': plate_data.get('height', 0),
                'capacity': f"{plate_data.get('capacity', 0)} кг/м²",
                'concrete': plate_data.get('concrete_class', ''),
                'wireTop': plate_data.get('wire_top', 0),
                'wireBottom': plate_data.get('wire_bottom', 0),
                'count': 1
            })

        # Get unplaced slabs (plates assigned to orders but not to tracks)
        unplaced_plates = Plate.objects.filter(order__isnull=False, track__isnull=True)
        unplaced_serializer = PlateSerializer(unplaced_plates, many=True)
        unplaced_slabs = []

        for plate_data in unplaced_serializer.data:
            unplaced_slabs.append({
                'id': plate_data['id'],
                'name': plate_data.get('name', ''),
                'length': plate_data.get('length', 0),
                'width': plate_data.get('width', 0),
                'height': plate_data.get('height', 0),
                'capacity': f"{plate_data.get('capacity', 0)} кг/м²",
                'concrete': plate_data.get('concrete_class', ''),
                'wireTop': plate_data.get('wire_top', 0),
                'wireBottom': plate_data.get('wire_bottom', 0),
                'count': 1,
                'order': plate_data.get('order', None)
            })

        return Response({
            'usedStock': used_stock,
            'availableStock': available_stock,
            'unplacedSlabs': unplaced_slabs
        })

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
                'icon': 'cubes',
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
                'icon': 'cubes',
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
                'icon': 'cog',
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
                'value': overall_stats['last_track'].strftime('%d.%m.%Y'),
                'icon': 'calendar-check',
                'color': 'blue'
            },
            # KPI metrics
            {
                'id': 10,
                'section': 'KPI расстановки плит',
                'title': 'Общий показатель эффективности',
                'value': f"{overall_stats['kpi_score']:.2f}",
                'icon': 'chart-line',
                'color': 'blue',
                'tooltip': 'Чем ниже значение, тем лучше расстановка'
            },
            {
                'id': 11,
                'section': 'KPI расстановки плит',
                'title': 'Экономия на типе бетона',
                'value': f"{overall_stats['kpi_concrete_economy']:.2f}",
                'icon': 'cubes',
                'color': 'green',
                'tooltip': 'Штраф за избыточное использование дорогих марок бетона'
            },
            {
                'id': 12,
                'section': 'KPI расстановки плит',
                'title': 'Экономия проволоки',
                'value': f"{overall_stats['kpi_wire_economy']:.2f}",
                'icon': 'grip-lines',
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
            print("claster_plan =", claster_plan, type(claster_plan))

            claster_plan()
        return Response({'status': 'success', 'message': 'Calculation successfully'})
