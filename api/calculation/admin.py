from django.contrib import admin

from .models.base import Customer, Export1c, Order, Deadline, Track, Plate, ReadyPlate
from .models.params import Parameters, UnitPrice, HolidayDate
from .models.calculation_status import CalculationStatus


class PlateInline(admin.TabularInline):
    model = Plate
    extra = 1


class TrackAdmin(admin.ModelAdmin):
    inlines = [PlateInline]


class ParametersAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('road_length', 'tracks_count', 'default_available_tracks',
                       'tail_length', 'force_tail', 'production_lag')
        }),
        ('Выходные дни', {
            'fields': ('monday_weekend', 'tuesday_weekend', 'wednesday_weekend', 'thursday_weekend',
                      'friday_weekend', 'saturday_weekend', 'sunday_weekend'),
            'description': 'Укажите, какие дни недели считать выходными (количество доступных дорожек будет 0)'
        }),
        ('Настройки 1C', {
            'fields': ('url_1c', 'url_1c_export', 'sign_1c'),
            'classes': ('grp-collapse grp-closed',),
        }),
    )

class Export1CAdmin(admin.ModelAdmin):
    list_filter = ['date']

admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(Deadline)
admin.site.register(Track, TrackAdmin)
admin.site.register(Plate)
admin.site.register(ReadyPlate)
admin.site.register(UnitPrice)
admin.site.register(Parameters, ParametersAdmin)
admin.site.register(HolidayDate)
admin.site.register(Export1c, Export1CAdmin)
admin.site.register(CalculationStatus)
