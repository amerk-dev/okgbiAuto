from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet, TrackViewSet, OrderViewSet, PlateViewSet, ReadyPlateViewSet,
    UnitPriceViewSet, ParametersViewSet, StockView, DashboardStatsView, CalculationView,
    CalculationStatusView, PrintTrackPlanView, PrintTrackPlanShortView, Export1CView, 
    AlgorithmView, AlgorithmDemoView
)


# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'plates', PlateViewSet)
router.register(r'ready-plates', ReadyPlateViewSet)
router.register(r'unit-prices', UnitPriceViewSet)
router.register(r'parameters', ParametersViewSet)
# MoveTrackView is an APIView, not a ViewSet, so it cannot be registered with the router
# It's already accessible via the move_slab_view wrapper on line 34

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),

    # Custom API views
    path('stock/', StockView.as_view(), name='stock'),
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('contractors/', CustomerViewSet.as_view({'get': 'list'}), name='contractors'),

    # Maintain compatibility with old API endpoints
    path('tracks/<int:pk>/contractor/', TrackViewSet.as_view({'post': 'update_contractor'}), name='update_track_contractor'),
    # Explicitly register the transfer_slabs action with the POST method
    path('tracks/transfer-slabs/', TrackViewSet.as_view({'post': 'transfer_slabs'}), name='transfer_slabs'),
    path('materials/', UnitPriceViewSet.as_view({'get': 'materials'}), name='materials'),
    path('materials/update/', UnitPriceViewSet.as_view({'post': 'update_materials'}), name='update_materials'),
    path('track-settings/', ParametersViewSet.as_view({'get': 'track_settings'}), name='track_settings'),
    path('track-settings/update/', ParametersViewSet.as_view({'post': 'update_track_settings'}), name='update_track_settings'),

    # Calculation endpoints
    path('calculate/', CalculationView.as_view(), name='calculate'),
    path('calculation-status/', CalculationStatusView.as_view(), name='calculation_status'),
    path('calculation-status/<str:task_id>/', CalculationStatusView.as_view(), name='calculation_status_detail'),

    # Print endpoints
    path('print/', PrintTrackPlanView.as_view(), name='print_track_plan'),
    path('print-short/', PrintTrackPlanShortView.as_view(), name='print_track_plan_short'),

    # Export to 1C endpoint
    path('export-1c/', Export1CView.as_view(), name='export_1c'),

    # Algorithm description and demo endpoints
    path('algorithm/', AlgorithmView.as_view(), name='algorithm'),
    path('algorithm/demo/', AlgorithmDemoView.as_view(), name='algorithm_demo'),
]
