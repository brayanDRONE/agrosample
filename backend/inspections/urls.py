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
    # Autenticación JWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Rutas del router
    path('', include(router.urls)),
]
