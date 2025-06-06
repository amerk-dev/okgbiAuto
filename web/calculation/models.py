import re
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.db.models import DecimalField


class Plate(models.Model):
    name = models.CharField(max_length=255)
    count = models.PositiveIntegerField()
    length = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    order = models.CharField(max_length=255, null=True, blank=True)
    concrete_class = models.CharField(max_length=10)
    wire_bottom = models.PositiveIntegerField()
    wire_top = models.PositiveIntegerField()

    class Meta:
        abstract = True


    @property
    def clean_name(self):
        pattern = r'\s*((\d+,{,1}\d*))\s*нагрузка'  # Удаляет число и слово "нагрузка" с пробелами

        cleaned_text = re.sub(pattern, '', self.name).strip()
        return cleaned_text


    @property
    def capacity(self):
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


class ProductionDay(models.Model):
    date = models.DateField()
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    useful_len = models.PositiveIntegerField()
    free_len = models.PositiveIntegerField()
    concrete_class = models.CharField(max_length=10)
    wire_bottom = models.PositiveIntegerField()
    wire_top = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=16, decimal_places=2)
    free_cost = models.DecimalField(max_digits=16, decimal_places=2)
    full_cost = models.DecimalField(max_digits=16, decimal_places=2)

    class Meta:
        verbose_name = "Production Day"
        verbose_name_plural = "Production Days"
        ordering = ['date']


class ProductionDayPlate(Plate):
    production_day = models.ForeignKey(ProductionDay, on_delete=models.CASCADE, related_name='plates')

    class Meta:
        verbose_name = "Production Day Plate"
        verbose_name_plural = "Production Day Plates"



class UsedReadyPlate(Plate):
    class Meta:
        verbose_name = "Used Ready Plate"
        verbose_name_plural = "Used Ready Plates"


class UnplacedPlate(Plate):
    class Meta:
        verbose_name = "Unplaced Plate"
        verbose_name_plural = "Unplaced Plates"


class LeftReadyPlate(Plate):
    class Meta:
        verbose_name = "Left Ready Plate"
        verbose_name_plural = "Left Ready Plates"


class DailyRetooling(models.Model):
    date = models.DateField()
    count = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=16, decimal_places=2)

    class Meta:
        verbose_name = "Daily Retooling"
        verbose_name_plural = "Daily Retoolings"

class DailyRetoolingChanges(models.Model):
    daily_retooling = models.ForeignKey(DailyRetooling, on_delete=models.CASCADE, related_name='changes')
    from_width = models.PositiveIntegerField()
    from_height = models.PositiveIntegerField()
    to_width = models.PositiveIntegerField()
    to_height = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Daily Retooling Changes"
        verbose_name_plural = "Daily Retoolings Changes"


class RetoolingInfo(models.Model):
    price = models.DecimalField(max_digits=16, decimal_places=2)
    last_state_width = models.PositiveIntegerField()
    last_state_height = models.PositiveIntegerField()
    daily_retoolings = models.ManyToManyField(DailyRetooling)

    class Meta:
        verbose_name = "Retooling Info"
        verbose_name_plural = "Retooling Infos"


class ProductionPlan(models.Model):
    plan = models.ManyToManyField(ProductionDay)
    used_ready_plates = models.ManyToManyField(UsedReadyPlate)
    unplaced_plates = models.ManyToManyField(UnplacedPlate)
    left_ready_plates = models.ManyToManyField(LeftReadyPlate)
    retooling_info = models.OneToOneField(RetoolingInfo, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Production Plan"
        verbose_name_plural = "Production Plans"


class UnitPrice(models.Model):
    class UnitTypeChoice(models.IntegerChoices):
        PLATE = 1, 'Плита'
        WIRE = 2, 'Проволока'
        RETOOLING = 3, 'Переналадка'

    name = models.CharField(max_length=255, verbose_name="Наименование")
    concrete_class = models.CharField(max_length=10, null=True, blank=True, verbose_name="Класс бетона")
    price = models.DecimalField(max_digits=16, decimal_places=2, verbose_name="Цена")
    unit = models.PositiveSmallIntegerField(verbose_name="Тип",
                                            choices=UnitTypeChoice.choices, default=1)

    def clean(self):
        if self.unit == self.UnitTypeChoice.PLATE and not self.concrete_class:
            raise ValidationError({
                'concrete_class': 'Укажите класс бетона'
            })

    @property
    def unit_name(self):
        unit_name_dict = {
            1: 'куб',
            2: "п.м",
            3: "раз",
        }
        return unit_name_dict[self.unit]

    class Meta:
        verbose_name = 'Цена за единицу'
        verbose_name_plural = 'Цены за единицу'

    def __str__(self):
        return f"{self.name} ({self.price} за 1 {self.unit_name})"


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Parameters(SingletonModel):
    road_length = models.PositiveIntegerField(verbose_name="Длина дорожки")
    default_available_tracks = models.PositiveIntegerField(default=4,
                                                           verbose_name='Количество дорожек по умолчанию')
    tracks_count = models.PositiveIntegerField(default=7, verbose_name="Количество дорожек")
    production_lag = models.PositiveIntegerField(default=3,
                                                verbose_name='Производственный лаг (в днях)')
    url_1c = models.CharField(max_length=255, verbose_name='URL 1c', default='')
    sign_1c = models.CharField(max_length=255, verbose_name='Пароль 1с', default='123456788')

    # Weekend day settings
    monday_weekend = models.BooleanField(default=False, verbose_name='Понедельник')
    tuesday_weekend = models.BooleanField(default=False, verbose_name='Вторник')
    wednesday_weekend = models.BooleanField(default=False, verbose_name='Среда')
    thursday_weekend = models.BooleanField(default=False, verbose_name='Четверг')
    friday_weekend = models.BooleanField(default=False, verbose_name='Пятница')
    saturday_weekend = models.BooleanField(default=True, verbose_name='Суббота')
    sunday_weekend = models.BooleanField(default=True, verbose_name='Воскресенье')

    class Meta:
        verbose_name = "Параметры"
        verbose_name_plural = "Параметры"

    def __str__(self):
        return "Главные параметры"

    def save(self, *args, **kwargs):
        prev_params = Parameters.get_solo()
        changes_made = False

        # Check if default_available_tracks has changed
        if prev_params.default_available_tracks != self.default_available_tracks:
            changes_made = True
            obj = super().save(*args, **kwargs)

            # Update all non-weekend days with the new default_available_tracks
            for track in AvailableTrack.objects.all():
                weekday = track.date.weekday()
                is_weekend = (
                    (weekday == 0 and self.monday_weekend) or
                    (weekday == 1 and self.tuesday_weekend) or
                    (weekday == 2 and self.wednesday_weekend) or
                    (weekday == 3 and self.thursday_weekend) or
                    (weekday == 4 and self.friday_weekend) or
                    (weekday == 5 and self.saturday_weekend) or
                    (weekday == 6 and self.sunday_weekend)
                )
                if not is_weekend:
                    track.count = self.default_available_tracks
                    track.save()

            return obj

        # Check if any weekend day settings have changed
        weekend_changes = (
            prev_params.monday_weekend != self.monday_weekend or
            prev_params.tuesday_weekend != self.tuesday_weekend or
            prev_params.wednesday_weekend != self.wednesday_weekend or
            prev_params.thursday_weekend != self.thursday_weekend or
            prev_params.friday_weekend != self.friday_weekend or
            prev_params.saturday_weekend != self.saturday_weekend or
            prev_params.sunday_weekend != self.sunday_weekend
        )

        if weekend_changes:
            changes_made = True
            obj = super().save(*args, **kwargs)

            # Update all tracks based on their weekday and the new weekend settings
            for track in AvailableTrack.objects.all():
                weekday = track.date.weekday()
                is_weekend = False

                if weekday == 0 and self.monday_weekend:
                    is_weekend = True
                elif weekday == 1 and self.tuesday_weekend:
                    is_weekend = True
                elif weekday == 2 and self.wednesday_weekend:
                    is_weekend = True
                elif weekday == 3 and self.thursday_weekend:
                    is_weekend = True
                elif weekday == 4 and self.friday_weekend:
                    is_weekend = True
                elif weekday == 5 and self.saturday_weekend:
                    is_weekend = True
                elif weekday == 6 and self.sunday_weekend:
                    is_weekend = True

                track.count = 0 if is_weekend else self.default_available_tracks
                track.save()

            return obj

        if not changes_made:
            return super().save(*args, **kwargs)


class Product(models.Model):
    """Базовая модель изделия (общие характеристики)"""
    name = models.CharField('Наименование', max_length=50)
    length = models.PositiveIntegerField('Длина, мм', validators=[MinValueValidator(1)])
    width = models.PositiveIntegerField('Ширина, мм', validators=[MinValueValidator(1)])
    height = models.PositiveIntegerField('Высота, мм', validators=[MinValueValidator(1)])
    concrete_class = models.CharField('Класс бетона', max_length=10)
    wire_bottom = models.PositiveIntegerField('Проволока верх, шт', validators=[MinValueValidator(1)])
    wire_top = models.PositiveIntegerField('Проволока низ, шт', validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Изделие'
        verbose_name_plural = 'Изделия'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'length', 'width', 'height', 'concrete_class', 'wire_top', 'wire_bottom'],
                name='unique_product'
            )
        ]

    @property
    def clean_name(self):
        pattern = r'\s*((\d+,{,1}\d*))\s*нагрузка'  # Удаляет число и слово "нагрузка" с пробелами

        cleaned_text = re.sub(pattern, '', self.name).strip()
        return cleaned_text


    @property
    def capacity(self):
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

    def __str__(self):
        return f"{self.clean_name} ({self.length}x{self.width}x{self.height}), бетон {self.concrete_class}"


class Order(models.Model):
    """Модель заказа"""
    order_number = models.CharField('Номер заказа', max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Изделие')
    count = models.PositiveIntegerField('Количество, шт', validators=[MinValueValidator(1)])
    deadline = models.DateField('Дедлайн по заказу', null=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['deadline']

    def __str__(self):
        return f"Заказ {self.order_number} - {self.product.name} x{self.count}"


class Inventory(models.Model):
    """Модель остатков на складе"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, verbose_name='Изделие', primary_key=True)
    count = models.PositiveIntegerField('Количество, шт', validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Остаток'
        verbose_name_plural = 'Остатки'

    def __str__(self):
        return f"Остаток: {self.product.clean_name} - {self.count} шт"


class AvailableTrack(models.Model):
    date = models.DateField()
    count = models.PositiveIntegerField()


    class Meta:
        ordering = ['date']


    @property
    def retooling_info(self):
        return DailyRetooling.objects.filter(date=self.date).first()

    @property
    def is_weekend_day(self):
        """Check if this day is marked as a weekend day in the admin panel"""
        params = Parameters.get_solo()
        weekday = self.date.weekday()  # 0 is Monday, 6 is Sunday

        if weekday == 0 and params.monday_weekend:
            return True
        elif weekday == 1 and params.tuesday_weekend:
            return True
        elif weekday == 2 and params.wednesday_weekend:
            return True
        elif weekday == 3 and params.thursday_weekend:
            return True
        elif weekday == 4 and params.friday_weekend:
            return True
        elif weekday == 5 and params.saturday_weekend:
            return True
        elif weekday == 6 and params.sunday_weekend:
            return True

        return False


    @classmethod
    def get_tracks(cls, date_from, date_to=None):
        params = Parameters.get_solo()
        date_to = date_to or date_from + timedelta(days=6)
        for day in range((date_to - date_from).days + 1):  # +1 to include date_to
            date = date_from + timedelta(days=day)
            # Check if the day is marked as a weekend day
            is_weekend = False
            weekday = date.weekday()  # 0 is Monday, 6 is Sunday

            if weekday == 0 and params.monday_weekend:
                is_weekend = True
            elif weekday == 1 and params.tuesday_weekend:
                is_weekend = True
            elif weekday == 2 and params.wednesday_weekend:
                is_weekend = True
            elif weekday == 3 and params.thursday_weekend:
                is_weekend = True
            elif weekday == 4 and params.friday_weekend:
                is_weekend = True
            elif weekday == 5 and params.saturday_weekend:
                is_weekend = True
            elif weekday == 6 and params.sunday_weekend:
                is_weekend = True

            # Set count to 0 for weekend days, otherwise use default_available_tracks
            track_count = 0 if is_weekend else params.default_available_tracks
            cls.objects.get_or_create(date=date, defaults={'count': track_count})

        tracks = cls.objects.filter(date__gte=date_from, date__lte=date_to)
        return tracks


class ErrorLog(models.Model):
    """Model for tracking errors in the application"""
    ERROR_SOURCES = [
        ('api', 'API'),
        ('1c', '1C'),
        ('calculation', 'Расчет'),
        ('view', 'Представление'),
        ('other', 'Другое'),
    ]

    error_type = models.CharField(max_length=255)
    error_message = models.TextField()
    source = models.CharField(max_length=255)
    traceback = models.TextField()
    details = models.TextField(blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Лог ошибок'
        verbose_name_plural = 'Логи ошибок'

    def __str__(self):
        return f"{self.error_type}: {self.error_message[:50]}"

    @property
    def short_error(self):
        return f"{self.error_message[:100]}{'...' if len(self.error_message) > 100 else ''}"


class ErrorReport(models.Model):
    """Model for storing user reports of errors"""
    error_log = models.ForeignKey(
        ErrorLog,
        on_delete=models.CASCADE,
        related_name='user_reports'
    )
    user_description = models.TextField()
    contact_info = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Отчет об ошибке'
        verbose_name_plural = 'Отчеты об ошибках'

    def __str__(self):
        return f"Report for {self.error_log.id} - {self.timestamp}"
