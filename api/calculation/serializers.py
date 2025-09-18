from rest_framework import serializers

from .models import (
    Customer, Order, Parameters, ReadyPlate, Track, UnitPrice, Plate
)
from .models.params import HolidayDate

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name']

class TrackSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = Track
        fields = ['id', 'position', 'day', 'customer', 'useful_length', 'free_length', 'is_manual']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add track properties
        if instance.plates.exists():
            data['width'] = instance.width
            data['height'] = instance.height
            data['wire_top'] = instance.wire_top
            data['wire_bottom'] = instance.wire_bottom
            data['concrete_class'] = instance.concrete_class
            data['cost'] = float(instance.cost)

            # Add formatted fields
            data['width_mm'] = f"{instance.width}мм"
            data['height_mm'] = f"{instance.height}мм"
            data['wire_top_mm'] = f"{instance.wire_top}мм"
            data['wire_bottom_mm'] = f"{instance.wire_bottom}мм"
            data['price'] = f"{instance.cost} ₽"
            data['status'] = 'overdue' if instance.has_overdue_deadline else 'booked'
            data['occupied'] = f"{instance.useful_length}мм"
            data['free'] = f"{instance.free_length}мм"

        return data

class PlateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plate
        fields = ['id', 'name', 'width', 'height', 'wire_top', 'wire_bottom', 
                 'concrete_class', 'deadline', 'track', 'is_deleted']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add track-related fields if track is assigned
        if instance.track:
            data['occupied'] = f"{instance.width}мм"
            data['free'] = f"{instance.track.useful_length - instance.width}мм"

        return data

class ReadyPlateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadyPlate
        fields = ['id', 'name', 'width', 'height', 'length', 'wire_top', 
                 'wire_bottom', 'concrete_class', 'capacity', 'is_deleted']

class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'is_deleted']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add deadline and complete date
        deadline = instance.last_deadline
        data['deadline'] = deadline.date.strftime('%d.%m.%Y') if deadline.date else ""

        complete_date = instance.complete_date
        data['complete_date'] = complete_date.strftime('%d.%m.%Y') if complete_date else ""

        # Get plates for this order
        plates = Plate.objects.filter(deadline__order=instance)
        if plates.exists():
            first_plate = plates.first()
            data['name'] = first_plate.name
            data['length'] = first_plate.length
            data['width'] = first_plate.width
            data['height'] = first_plate.height
            data['capacity'] = f'{first_plate.capacity} кг/м²'
            data['concrete'] = first_plate.concrete_class
            data['wire_top'] = first_plate.wire_top
            data['wire_bottom'] = first_plate.wire_bottom

        data['slab_count'] = plates.count()
        data['status'] = 'Просрочен' if instance.is_overdue else ('В производстве' if plates.filter(track__isnull=False).exists() else 'Ожидает')
        data['status_class'] = 'bg-red-100 text-red-800' if instance.is_overdue else ('bg-green-100 text-green-800' if plates.filter(track__isnull=False).exists() else 'bg-yellow-100 text-yellow-800')

        return data

class UnitPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitPrice
        fields = ['id', 'name', 'concrete_class', 'price', 'unit']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add unit name
        data['unit_name'] = instance.unit_name
        return data

class HolidayDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HolidayDate
        fields = ['id', 'date']

class ParametersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameters
        fields = [
            'road_length', 'tracks_count', 'default_available_tracks',
            'production_lag', 'tail_length',
            'monday_weekend', 'tuesday_weekend', 'wednesday_weekend', 
            'thursday_weekend', 'friday_weekend', 'saturday_weekend', 'sunday_weekend'
        ]
