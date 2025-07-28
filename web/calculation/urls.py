from django.urls import path

from .error_views import (error_list, report_error, resolve_error, view_error)
from .views import (algorithm, algorithm_demo, change_available_tracks, delete_order, delete_plate, 
                   export_to_1c_view, fetch_and_save_production_plan, generate_production_calendar, 
                   index, move_plate, restore_order, restore_plate)

urlpatterns = [
    path('index/', index, name='index'),
    path('fetch-production-plan/', fetch_and_save_production_plan, name='fetch_production_plan'),
    path('change-available-tracks/', change_available_tracks, name='change_available_tracks'),
    path('generate-production-calendar/', generate_production_calendar, name='generate_production_calendar'),

    # Algorithm URLs
    path('algorithm/', algorithm, name='algorithm'),
    path('algorithm-demo/', algorithm_demo, name='algorithm_demo'),

    # Order management URLs
    path('delete-order/<int:order_id>/', delete_order, name='delete_order'),
    path('restore-order/<int:order_id>/', restore_order, name='restore_order'),

    # Plate management URLs
    path('delete-plate/<str:plate_type>/<int:plate_id>/', delete_plate, name='delete_plate'),
    path('restore-plate/<str:plate_type>/<int:plate_id>/', restore_plate, name='restore_plate'),
    path('move-plate/', move_plate, name='move_plate'),
    path('export-to-1c/', export_to_1c_view, name='export_to_1c'),

    # Error handling URLs
    path('report-error/<int:error_id>/', report_error, name='report_error'),
    path('error-list/', error_list, name='error_list'),
    path('error/<int:error_id>/', view_error, name='view_error'),
    path('resolve-error/<int:error_id>/', resolve_error, name='resolve_error'),
]
