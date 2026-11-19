"""
URLs para la aplicación inspections.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    EstablishmentViewSet,
    InspectionViewSet,
    SamplingResultViewSet,
    MuestreoViewSet,
    ThemeViewSet,
    DispatchFlatFileViewSet
)
from .views_admin import (
    CustomTokenObtainPairView,
    AdminDashboardViewSet,
    AdminEstablishmentViewSet,
    AdminThemeViewSet,
    CurrentUserViewSet
)
from . import plan_views

router = DefaultRouter()
router.register(r'establishments', EstablishmentViewSet, basename='establishment')
router.register(r'inspections', InspectionViewSet, basename='inspection')
router.register(r'sampling-results', SamplingResultViewSet, basename='samplingresult')
router.register(r'muestreo', MuestreoViewSet, basename='muestreo')
router.register(r'themes', ThemeViewSet, basename='theme')
router.register(r'dispatch-flatfile', DispatchFlatFileViewSet, basename='dispatch-flatfile')

# Rutas de administración
router.register(r'admin/dashboard', AdminDashboardViewSet, basename='admin-dashboard')
router.register(r'admin/establishments', AdminEstablishmentViewSet, basename='admin-establishments')
router.register(r'admin/themes', AdminThemeViewSet, basename='admin-themes')
router.register(r'users/current', CurrentUserViewSet, basename='current-user')

urlpatterns = [
    path('plans/account/', plan_views.account_plan, name='plan-account'),
    path('plans/alert/acknowledge/', plan_views.acknowledge_plan_alert, name='plan-alert-acknowledge'),
    path('plans/reserve/', plan_views.reserve_client_operation, name='plan-reserve'),
    path('plans/reservations/<int:usage_id>/dispatch-print/', plan_views.dispatch_print, name='plan-dispatch-print'),
    path('plans/reservations/<int:usage_id>/finish/', plan_views.finish_client_operation, name='plan-finish'),
    path('plans/batch-pdf/<uuid:artifact_id>/', plan_views.download_batch_pdf, name='plan-batch-pdf'),
    # Autenticación JWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Rutas del router
    path('', include(router.urls)),
]
