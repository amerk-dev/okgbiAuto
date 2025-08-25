import re
from datetime import datetime, timedelta, date
from decimal import Decimal

from django.db import models, transaction
# from django.utils.functional import property

from .params import Parameters, UnitPrice


class Customer(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Order(models.Model):
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    order_number = models.CharField('Номер заказа', max_length=50)
    is_deleted = models.BooleanField('Удален', default=False)

    def __str__(self):
        s = f"Order {self.id}"
        if self.customer:
            s += f"- {self.customer.name}"
        return  s

    @property
    def is_overdue(self):
        return any([plate.is_overdue for plate in self.deadlines.all()])

    @property
    def complete_date(self):
        return max([deadline.complete_date for deadline in self.deadlines.all()])

    @property
    def last_deadline(self):
        return self.deadlines.last()


class Deadline(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deadlines')
    date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return str(self.date)

    @property
    def is_overdue(self):
        return any([plate.is_overdue for plate in self.plates.all()])

    @property
    def complete_date(self):
        return max([plate.track.day for plate in self.plates.all() if plate.track], default=None)



class Track(models.Model):
    position = models.PositiveSmallIntegerField()
    day = models.DateField()
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    is_manual = models.BooleanField(default=False)

    def __str__(self):
        return f"Track {self.position} - {self.day}"

    class Meta:
        ordering = ['day']

    @classmethod
    def recreate_tracks(cls):
        params = Parameters.get_solo()
        weekend_settings = [
            (0, 'monday_weekend'),
            (1, 'tuesday_weekend'),
            (2, 'wednesday_weekend'),
            (3, 'thursday_weekend'),
            (4, 'friday_weekend'),
            (5, 'saturday_weekend'),
            (6, 'sunday_weekend')
        ]

        with transaction.atomic():
            days = 100
            cls.objects.all().delete()

            new_tracks = []
            for day_step in range(days):
                day = date.today() + timedelta(days=day_step)

                # Проверяем, является ли день выходным
                is_weekend = any(
                    day.weekday() == day_num and getattr(params, day_attr)
                    for day_num, day_attr in weekend_settings
                )

                if is_weekend:
                    continue
                for position in range(params.default_available_tracks):
                    new_tracks.append(Track(
                        day=day,
                        position=position
                    ))
            cls.objects.bulk_create(new_tracks)

    @classmethod
    def get_tracks(cls):
        return cls.objects.all()

    @property
    def deadline(self):
        params = Parameters.get_solo()
        deadline = min(self.plates.filter(deadline__date__isnull=False).values_list('deadline__date', flat=True), default=None)
        if deadline:
            deadline = deadline - timedelta(days=params.production_lag)
        return deadline

    @property
    def has_overdue_deadline(self):
        return any([plate.is_overdue for plate in self.plates.all()])

    @property
    def is_weekend_day(self):
        return Parameters.check_is_weekend_day(self.day)

    @classmethod
    def get_today_tracks(cls):
        return cls.objects.filter(day=datetime.today().date())

    @classmethod
    def get_current_week_tracks(cls):
        """
        Returns tracks for the current week (Monday to Sunday).
        """
        today = datetime.today().date()
        # Get the start of the week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        # Get the end of the week (Sunday)
        end_of_week = start_of_week + timedelta(days=6)

        return cls.objects.filter(day__gte=start_of_week, day__lte=end_of_week)

    @property
    def useful_length(self):
        return sum([plate.length for plate in self.plates.all()])

    @property
    def free_length(self):
        return Parameters.get_solo().road_length - self.useful_length

    @property
    def retoolings(self):
        retoolings = []
        for plate in self.plates.all():
            if (plate.width, plate.height) not in retoolings:
                retoolings.append((plate.width, plate.height))
        return retoolings

    @property
    def retoolings_price(self):
        return len(self.retoolings) * UnitPrice.get_retooling_price()

    @property
    def cost(self):
        wire_price = UnitPrice.get_wire_price()
        plate_class_prices = UnitPrice.get_plates_prices()

        plates = self.plates.all()
        wire_top_max = self.wire_top
        wire_bottom_max = self.wire_bottom
        using_plate_classes = set(plate.concrete_class for plate in plates)
        plate_price = max([plate_class_prices[plate_class] for plate_class in using_plate_classes], default=0)

        plate_volume = (self.useful_length * plates[0].height * plates[0].width) / 10**9 if plates else 0
        plate_cost = Decimal(str(plate_volume)) * Decimal('0.65') * plate_price
        wire_cost = Decimal(str(wire_top_max + wire_bottom_max)) * wire_price * Decimal(str(self.useful_length / 1000))
        return plate_cost + wire_cost + self.retoolings_price

    @property
    def concrete_class(self):
        plate_class_prices = UnitPrice.get_plates_prices()
        using_plate_classes = set(plate.concrete_class for plate in self.plates.all())
        return max(using_plate_classes, key=lambda plate_class: plate_class_prices[plate_class])


    @property
    def width(self):
        return self.plates.all()[0].width if self.plates.exists() else None

    @property
    def height(self):
        return self.plates.all()[0].height if self.plates.exists() else None

    @property
    def wire_top(self):
        plates = self.plates.all()
        wire_top_max = max([int(plate.wire_top) for plate in plates], default=0)
        return wire_top_max

    @property
    def wire_bottom(self):
        plates = self.plates.all()
        wire_bottom_max = max([int(plate.wire_bottom) for plate in plates], default=0)
        return wire_bottom_max

    @property
    def get_size(self):
        return self.width, self.height

    @property
    def overendering_wire_kg(self):
        params = Parameters.get_solo()
        wire_top_max = self.wire_top
        wire_bottom_max = self.wire_bottom
        length = Decimal(str(params.road_length)) / 1000

        corrent_useful_kg = length * (wire_top_max + wire_bottom_max) * Decimal("0.156")

        needed_wire_kg = 0
        for plate in self.plates.all():
            needed_wire_kg += Decimal(str(plate.length)) / 1000 * (wire_top_max + wire_bottom_max)
        return corrent_useful_kg - needed_wire_kg * Decimal("0.156")

class AbstractPlate(models.Model):
    name = models.CharField(max_length=255)
    length = models.FloatField()
    width = models.FloatField()
    concrete_class = models.CharField(max_length=50)
    wire_bottom = models.CharField(max_length=50)
    wire_top = models.CharField(max_length=50)
    height = models.FloatField()

    def __str__(self):
        return f'name - {self.name}, l - {self.length}, w:{self.width}, h:{self.height}, {self.concrete_class}, wb-{self.wire_bottom}, wt-{self.wire_top}'

    class Meta:
        abstract = True

    @property
    def clean_name(self):
        """Remove load information from name"""
        pattern = r'\s*((\d+,{,1}\d*))\s*нагрузка'  # Удаляет число и слово "нагрузка" с пробелами
        cleaned_text = re.sub(pattern, '', self.name).strip()
        return cleaned_text

    @property
    def capacity(self):
        """Extract load capacity from name"""
        pattern = r'((\d+,{,1}\d*))\s*нагрузка'
        match = re.search(pattern, self.name)
        if match:
            number = match.group(1)
            try:
                return int(number)
            except ValueError:
                return float(number.replace(',', '.'))
        else:
            return 0

class Plate(AbstractPlate):
    track = models.ForeignKey(Track, on_delete=models.SET_NULL, null=True, related_name='plates')
    deadline = models.ForeignKey(Deadline, on_delete=models.CASCADE, related_name='plates')


    @property
    def is_overdue(self):
        parameters = Parameters.get_solo()
        return (self.deadline.date
                and self.deadline.date < (self.track.day + timedelta(days=parameters.production_lag)))


class ReadyPlate(AbstractPlate):
    pass
