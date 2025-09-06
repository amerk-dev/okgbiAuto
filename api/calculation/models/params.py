from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils import timezone


class UnitTypeChoice(models.IntegerChoices):
    PLATE = 1, 'Плита'
    WIRE = 2, 'Проволока'
    RETOOLING = 3, 'Переналадка'

class UnitPrice(models.Model):

    name = models.CharField(max_length=255, verbose_name="Наименование")
    concrete_class = models.CharField(max_length=10, null=True, blank=True, verbose_name="Класс бетона")
    price = models.DecimalField(max_digits=16, decimal_places=2, verbose_name="Цена")
    unit = models.PositiveSmallIntegerField(verbose_name="Тип",
                                            choices=UnitTypeChoice.choices, default=1)

    def clean(self):
        if self.unit == UnitTypeChoice.PLATE and not self.concrete_class:
            raise ValidationError({
                'concrete_class': 'Укажите класс бетона'
            })

    @cached_property
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
        constraints = [
            models.UniqueConstraint(
                fields=['unit'],
                condition=models.Q(unit=UnitTypeChoice.RETOOLING),
                name='unique_retooling_unit'
            ),
            models.UniqueConstraint(
                fields=['unit'],
                condition=models.Q(unit=UnitTypeChoice.WIRE),
                name='unique_wire_unit'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.price} за 1 {self.unit_name})"


    @classmethod
    def get_retooling_price(cls):
        return cls.objects.get(unit=UnitTypeChoice.RETOOLING).price

    @classmethod
    def get_wire_price(cls):
        return cls.objects.get(unit=UnitTypeChoice.WIRE).price

    @classmethod
    def get_plates_prices(cls):
        return {
            plate.concrete_class: plate.price
            for plate in cls.objects.filter(unit=UnitTypeChoice.PLATE)
        }


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
    tail_length = models.PositiveIntegerField(default=2000,
                                           help_text='Критическая длина хвоста в мм., при превышении которой'
                                                     ' хвост будет перенесен в конец',
                                           verbose_name='Длина хвоста')
    FORCE_TAIL_CHOICES = [
        (0, 'Мягкий режим'),
        (1, 'Средний режим'),
        (2, 'Жесткий режим'),
    ]
    force_tail = models.IntegerField(default=0,
                                     choices=FORCE_TAIL_CHOICES,
                                     verbose_name='Режим переноса хвоста',
                                     help_text='0 - мягкий режим, 1 - средний режим, 2 - жесткий режим')
    url_1c = models.CharField(max_length=255, verbose_name='URL 1c', default='')
    url_1c_export = models.CharField(max_length=255, verbose_name='URL 1c', default='')
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
        constraints = [models.CheckConstraint(
            check=models.Q(tracks_count__gte=models.F('default_available_tracks')),
            name='check_tracks_count',
            violation_error_message='Количество дорожек должно быть больше количества дорожек по умолчанию')]

    def __str__(self):
        return "Главные параметры"

    @staticmethod
    def check_is_weekend_day(date):
        """Check if a date is marked as a weekend day in the admin panel or is a holiday"""
        params = Parameters.get_solo()
        weekday = date.weekday()  # 0 is Monday, 6 is Sunday

        weekend_settings = [
            (0, params.monday_weekend),
            (1, params.tuesday_weekend),
            (2, params.wednesday_weekend),
            (3, params.thursday_weekend),
            (4, params.friday_weekend),
            (5, params.saturday_weekend),
            (6, params.sunday_weekend)
        ]

        # Check if it's a regular weekend day
        is_weekend = any(day == weekday and is_weekend for day, is_weekend in weekend_settings)

        # Check if it's a holiday
        is_holiday = HolidayDate.objects.filter(date=date).exists()

        return is_weekend or is_holiday


class HolidayDate(models.Model):
    """Model to store specific dates marked as holidays"""
    date = models.DateField(unique=True, verbose_name="Дата")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Выходной день"
        verbose_name_plural = "Выходные дни"
        ordering = ['date']

    def __str__(self):
        return self.date.strftime("%d.%m.%Y")
