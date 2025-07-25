import re
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.db.models import DecimalField


class BaseProductMixin(models.Model):
    """Base mixin for product-related models with common fields and methods"""
    name = models.CharField(max_length=255)
    length = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    concrete_class = models.CharField(max_length=10)
    wire_bottom = models.PositiveIntegerField()
    wire_top = models.PositiveIntegerField()

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


class Plate(BaseProductMixin):
    """Base model for all plate types"""
    count = models.PositiveIntegerField()
    order = models.CharField(max_length=255, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    # Add a type field to distinguish between different plate types
    PLATE_TYPE_CHOICES = [
        ('production', 'Production Day Plate'),
        ('used', 'Used Ready Plate'),
        ('unplaced', 'Unplaced Plate'),
        ('left', 'Left Ready Plate'),
    ]
    plate_type = models.CharField(max_length=20, choices=PLATE_TYPE_CHOICES, default='production')

    class Meta:
        verbose_name = "Plate"
        verbose_name_plural = "Plates"

    def __str__(self):
        return f"{self.name} ({self.length}x{self.width}x{self.height}), {self.count} шт."


class ProductionDay(models.Model):
    """Model representing a production day on a specific track"""
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
    # Relationship to plates is defined through the ProductionDayPlate model

    class Meta:
        verbose_name = "Production Day"
        verbose_name_plural = "Production Days"
        ordering = ['date']

    def __str__(self):
        return f"Production Day {self.date} - {self.useful_len}/{self.free_len + self.useful_len}"


class ProductionDayPlate(Plate):
    """Plate assigned to a specific production day"""
    production_day = models.ForeignKey(ProductionDay, on_delete=models.CASCADE, related_name='plates')

    class Meta:
        verbose_name = "Production Day Plate"
        verbose_name_plural = "Production Day Plates"

    def save(self, *args, **kwargs):
        self.plate_type = 'production'
        super().save(*args, **kwargs)


class UsedReadyPlate(Plate):
    """Plate that has been used from ready inventory"""
    class Meta:
        verbose_name = "Used Ready Plate"
        verbose_name_plural = "Used Ready Plates"

    def save(self, *args, **kwargs):
        self.plate_type = 'used'
        super().save(*args, **kwargs)


class UnplacedPlate(Plate):
    """Plate that couldn't be placed in the production plan"""
    class Meta:
        verbose_name = "Unplaced Plate"
        verbose_name_plural = "Unplaced Plates"

    def save(self, *args, **kwargs):
        self.plate_type = 'unplaced'
        super().save(*args, **kwargs)


class LeftReadyPlate(Plate):
    """Plate that is left over after production"""
    class Meta:
        verbose_name = "Left Ready Plate"
        verbose_name_plural = "Left Ready Plates"

    def save(self, *args, **kwargs):
        self.plate_type = 'left'
        super().save(*args, **kwargs)


class DailyRetooling(models.Model):
    """Model representing retooling operations for a specific date"""
    date = models.DateField()
    count = models.PositiveIntegerField(help_text="Number of retooling operations on this date")
    price = models.DecimalField(max_digits=16, decimal_places=2, help_text="Total cost of retooling operations")

    class Meta:
        verbose_name = "Daily Retooling"
        verbose_name_plural = "Daily Retoolings"
        ordering = ['date']

    def __str__(self):
        return f"Retooling on {self.date}: {self.count} operations, {self.price}"


class DailyRetoolingChanges(models.Model):
    """Model representing specific changes made during a retooling operation"""
    daily_retooling = models.ForeignKey(DailyRetooling, on_delete=models.CASCADE, related_name='changes')
    from_width = models.PositiveIntegerField(help_text="Original width setting")
    from_height = models.PositiveIntegerField(help_text="Original height setting")
    to_width = models.PositiveIntegerField(help_text="New width setting")
    to_height = models.PositiveIntegerField(help_text="New height setting")

    class Meta:
        verbose_name = "Retooling Change"
        verbose_name_plural = "Retooling Changes"

    def __str__(self):
        return f"Change from {self.from_width}x{self.from_height} to {self.to_width}x{self.to_height}"


class RetoolingInfo(models.Model):
    """Model containing aggregated information about retooling operations"""
    price = models.DecimalField(max_digits=16, decimal_places=2, help_text="Total cost of all retooling operations")
    last_state_width = models.PositiveIntegerField(help_text="Last width setting after retooling")
    last_state_height = models.PositiveIntegerField(help_text="Last height setting after retooling")
    daily_retoolings = models.ManyToManyField(DailyRetooling)

    class Meta:
        verbose_name = "Retooling Info"
        verbose_name_plural = "Retooling Info"

    def __str__(self):
        return f"Retooling Info: {self.price}, Last state: {self.last_state_width}x{self.last_state_height}"




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

    def save(self, *args, **kwargs):
        prev_params = Parameters.get_solo()

        # Проверяем изменения в настройках доступных дорожек или выходных дней
        tracks_changed = prev_params.default_available_tracks != self.default_available_tracks

        weekend_settings = [
            (0, 'monday_weekend'),
            (1, 'tuesday_weekend'),
            (2, 'wednesday_weekend'),
            (3, 'thursday_weekend'),
            (4, 'friday_weekend'),
            (5, 'saturday_weekend'),
            (6, 'sunday_weekend')
        ]

        weekend_changed = any(
            getattr(prev_params, day_attr) != getattr(self, day_attr)
            for _, day_attr in weekend_settings
        )

        if tracks_changed or weekend_changed:
            # Сначала сохраняем объект
            obj = super().save(*args, **kwargs)

            # Обновляем все дорожки на основе новых настроек
            for track in AvailableTrack.objects.all():
                weekday = track.date.weekday()

                # Проверяем, является ли день выходным
                is_weekend = any(
                    weekday == day_num and getattr(self, day_attr)
                    for day_num, day_attr in weekend_settings
                )

                # Устанавливаем количество дорожек в зависимости от того, выходной день или нет
                track.count = 0 if is_weekend else self.default_available_tracks
                track.save()

            return obj
        else:
            # Если никаких изменений не было, просто сохраняем объект
            return super().save(*args, **kwargs)


class Product(BaseProductMixin):
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

    def __str__(self):
        return f"{self.clean_name} ({self.length}x{self.width}x{self.height}), бетон {self.concrete_class}"


class Contractor(models.Model):
    """Модель контрагента"""
    name = models.CharField('Наименование', max_length=100)
    contact_info = models.CharField('Контактная информация', max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'
        ordering = ['name']

    def __str__(self):
        return self.name


class Order(models.Model):
    """Модель заказа"""
    order_number = models.CharField('Номер заказа', max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Изделие')
    count = models.PositiveIntegerField('Количество, шт', validators=[MinValueValidator(1)])
    deadline = models.DateField('Дедлайн по заказу', null=True)
    contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE, verbose_name='Контрагент', null=True)
    is_deleted = models.BooleanField('Удален', default=False)

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
    """Model representing available tracks for production on a specific date"""
    date = models.DateField()
    count = models.PositiveIntegerField()
    contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, verbose_name='Контрагент', null=True, blank=True)
    is_favorite = models.BooleanField('Избранная', default=False)

    class Meta:
        ordering = ['date']
        verbose_name = "Available Track"
        verbose_name_plural = "Available Tracks"

    def __str__(self):
        return f"Tracks on {self.date}: {self.count}"

    @property
    def retooling_info(self):
        """Get retooling information for this date"""
        return DailyRetooling.objects.filter(date=self.date).first()

    @staticmethod
    def check_is_weekend_day(date):
        """Check if a date is marked as a weekend day in the admin panel"""
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

        return any(day == weekday and is_weekend for day, is_weekend in weekend_settings)

    @property
    def is_weekend_day(self):
        """Check if this track's date is a weekend day"""
        return self.check_is_weekend_day(self.date)

    @classmethod
    def get_tracks(cls, date_from, date_to=None):
        """Get or create tracks for a date range"""
        params = Parameters.get_solo()
        date_to = date_to or date_from + timedelta(days=6)

        # Create tracks for each day in the range
        for day in range((date_to - date_from).days + 1):  # +1 to include date_to
            date = date_from + timedelta(days=day)
            # Set count to 0 for weekend days, otherwise use default_available_tracks
            track_count = 0 if cls.check_is_weekend_day(date) else params.default_available_tracks
            cls.objects.get_or_create(date=date, defaults={'count': track_count})

        # Return all tracks in the date range
        return cls.objects.filter(date__gte=date_from, date__lte=date_to)


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
