from django.contrib import admin
from django.conf import settings

from .models import (LeftReadyPlate, ProductionDay, ProductionDayPlate, RetoolingInfo, UnplacedPlate,
                     UsedReadyPlate, Parameters, UnitPrice, Order, Product, Inventory, AvailableTrack)


class DailyRetoolingInline(admin.TabularInline):
    model = RetoolingInfo.daily_retoolings.through
    extra = 0
    fields = ('dailyretooling', 'date', 'count', 'price')
    readonly_fields = fields

    def date(self, instance):
        return instance.dailyretooling.date

    date.short_description = 'Date'

    def count(self, instance):
        return instance.dailyretooling.count

    count.short_description = 'Count'

    def price(self, instance):
        return instance.dailyretooling.price

    price.short_description = 'Price'


class RetoolingInfoAdmin(admin.ModelAdmin):
    list_display = ('price', 'last_state_width', 'last_state_height')
    inlines = [DailyRetoolingInline]
    readonly_fields = ('price', 'last_state_width', 'last_state_height')

    # Убираем стандартное поле many-to-many из формы
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'daily_retoolings' in form.base_fields:
            del form.base_fields['daily_retoolings']
        return form

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}


# Остальной код admin.py остается без изменений
class ProductionDayPlateInline(admin.TabularInline):
    model = ProductionDayPlate
    extra = 0
    fields = ('name', 'count', 'length', 'width', 'height', 'order', 'concrete_class', 'wire_bottom', 'wire_top')
    readonly_fields = fields


class ProductionDayAdmin(admin.ModelAdmin):
    list_display = ('date', 'height', 'width', 'useful_len', 'free_len', 'concrete_class')
    list_filter = ('date', 'concrete_class')
    search_fields = ('date', 'concrete_class')
    inlines = [ProductionDayPlateInline]
    readonly_fields = ('total_cost', 'free_cost', 'full_cost')

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}


class UsedReadyPlateAdmin(admin.ModelAdmin):
    list_display = ('name', 'count', 'length', 'width', 'height', 'order', 'concrete_class')
    list_filter = ('concrete_class', 'order')
    search_fields = ('name', 'order')

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}


class UnplacedPlateAdmin(admin.ModelAdmin):
    list_display = ('name', 'count', 'length', 'width', 'height', 'order', 'concrete_class')
    list_filter = ('concrete_class', 'order')
    search_fields = ('name', 'order')

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}


class LeftReadyPlateAdmin(admin.ModelAdmin):
    list_display = ('name', 'count', 'length', 'width', 'height', 'order', 'concrete_class')
    list_filter = ('concrete_class', 'order')
    search_fields = ('name', 'order')

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}






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
            'fields': ('url_1c', 'sign_1c'),
            'classes': ('grp-collapse grp-closed',),
        }),
    )

admin.site.register(ProductionDay, ProductionDayAdmin)
admin.site.register(UsedReadyPlate, UsedReadyPlateAdmin)
admin.site.register(UnplacedPlate, UnplacedPlateAdmin)
admin.site.register(LeftReadyPlate, LeftReadyPlateAdmin)
admin.site.register(RetoolingInfo, RetoolingInfoAdmin)
admin.site.register(Inventory)
admin.site.register(Product)
admin.site.register(AvailableTrack)

admin.site.register(UnitPrice)
admin.site.register(Parameters, ParametersAdmin)
