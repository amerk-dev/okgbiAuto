from django.urls import path

from .error_views import (error_list, report_error, resolve_error, view_error)
from .views import (change_available_tracks, fetch_and_save_production_plan, generate_production_calendar, index)

urlpatterns = [
    path('index/', index, name='index'),
    path('fetch-production-plan/', fetch_and_save_production_plan, name='fetch_production_plan'),
    path('change-available-tracks/', change_available_tracks, name='change_available_tracks'),
    path('generate-production-calendar/', generate_production_calendar, name='generate_production_calendar'),

    # Error handling URLs
    path('report-error/<int:error_id>/', report_error, name='report_error'),
    path('error-list/', error_list, name='error_list'),
    path('error/<int:error_id>/', view_error, name='view_error'),
    path('resolve-error/<int:error_id>/', resolve_error, name='resolve_error'),
]
