"""
Vistas para el panel de administración (Superadmin).
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Establishment, EstablishmentTheme, UserProfile, Inspection
from .serializers_admin import (
    EstablishmentDetailSerializer,
    EstablishmentCreateSerializer,
    EstablishmentThemeSerializer,
    UserSerializer,
    UserProfileSerializer,
    DashboardStatsSerializer
)


class IsSuperAdmin(permissions.BasePermission):
    """Permiso: solo superadministradores."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_superadmin()
        )


class IsEstablishmentAdmin(permissions.BasePermission):
    """Permiso: administrador de establecimiento."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_establishment_admin()
        )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para JWT con información del usuario."""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar información del usuario
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        
        # Agregar rol si tiene perfil
        if hasattr(self.user, 'profile'):
            data['user']['role'] = self.user.profile.role
            data['user']['is_superadmin'] = self.user.profile.is_superadmin()
            data['user']['is_establishment_admin'] = self.user.profile.is_establishment_admin()
            data['user']['sample_label_text'] = self.user.profile.sample_label_text or 'MUESTRA USDA'
        
        establishment = None
        
        # Buscar establecimiento: primero como admin, luego en el perfil
        if hasattr(self.user, 'establishment_admin'):
            establishment = self.user.establishment_admin
        elif hasattr(self.user, 'profile') and self.user.profile.establishment:
            establishment = self.user.profile.establishment
        
        # Agregar establecimiento si existe
        if establishment:
            data['user']['establishment'] = {
                'id': establishment.id,
                'nombre': establishment.planta_fruticola,
                'exportadora': establishment.exportadora or '',
                'has_active_subscription': establishment.has_active_subscription()
            }
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener token JWT."""
    serializer_class = CustomTokenObtainPairSerializer


class AdminDashboardViewSet(viewsets.ViewSet):
    """ViewSet para el dashboard del superadmin."""
    permission_classes = [IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtiene estadísticas generales del sistema."""
        
        # Establecimientos
        total_establishments = Establishment.objects.count()
        active_establishments = Establishment.objects.filter(
            subscription_status='ACTIVE'
        ).count()
        
        # Establecimientos por vencer (próximos 7 días)
        today = timezone.now().date()
        expiring_date = today + timedelta(days=7)
        expiring_soon = Establishment.objects.filter(
            subscription_status='ACTIVE',
            subscription_expiry__gte=today,
            subscription_expiry__lte=expiring_date
        ).count()
        
        # Establecimientos expirados
        expired_establishments = Establishment.objects.filter(
            Q(subscription_status='EXPIRED') |
            Q(subscription_expiry__lt=today)
        ).count()
        
        # Inspecciones
        total_inspections = Inspection.objects.count()
        
        # Inspecciones este mes
        first_day_month = today.replace(day=1)
        inspections_this_month = Inspection.objects.filter(
            created_at__gte=first_day_month
        ).count()
        
        stats_data = {
            'total_establishments': total_establishments,
            'active_establishments': active_establishments,
            'expiring_soon': expiring_soon,
            'expired_establishments': expired_establishments,
            'total_inspections': total_inspections,
            'inspections_this_month': inspections_this_month,
        }
        
        serializer = DashboardStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Obtiene actividad reciente del sistema."""
        
        # Últimas 10 inspecciones
        recent_inspections = Inspection.objects.select_related(
            'establishment'
        ).order_by('-created_at')[:10]
        
        from .serializers import InspectionSerializer
        
        return Response({
            'recent_inspections': InspectionSerializer(recent_inspections, many=True).data
        })


class AdminEstablishmentViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de establecimientos (Superadmin)."""
    permission_classes = [IsSuperAdmin]
    queryset = Establishment.objects.all().select_related('admin_user', 'theme')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EstablishmentCreateSerializer
        return EstablishmentDetailSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Lista establecimientos con suscripción activa."""
        establishments = self.queryset.filter(subscription_status='ACTIVE')
        serializer = self.get_serializer(establishments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Lista establecimientos próximos a vencer."""
        today = timezone.now().date()
        expiring_date = today + timedelta(days=7)
        
        establishments = self.queryset.filter(
            subscription_status='ACTIVE',
            subscription_expiry__gte=today,
            subscription_expiry__lte=expiring_date
        )
        serializer = self.get_serializer(establishments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Lista establecimientos expirados."""
        today = timezone.now().date()
        
        establishments = self.queryset.filter(
            Q(subscription_status='EXPIRED') |
            Q(subscription_expiry__lt=today)
        )
        serializer = self.get_serializer(establishments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def renew_subscription(self, request, pk=None):
        """Renueva la suscripción de un establecimiento."""
        establishment = self.get_object()
        
        days = request.data.get('days', 30)
        
        if establishment.subscription_expiry:
            # Si aún no ha expirado, extender desde la fecha actual de expiración
            if establishment.subscription_expiry >= timezone.now().date():
                new_expiry = establishment.subscription_expiry + timedelta(days=days)
            else:
                # Si ya expiró, comenzar desde hoy
                new_expiry = timezone.now().date() + timedelta(days=days)
        else:
            new_expiry = timezone.now().date() + timedelta(days=days)
        
        establishment.subscription_expiry = new_expiry
        establishment.subscription_status = 'ACTIVE'
        establishment.save()
        
        serializer = self.get_serializer(establishment)
        return Response({
            'success': True,
            'message': f'Suscripción renovada por {days} días',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspende un establecimiento."""
        establishment = self.get_object()
        establishment.subscription_status = 'SUSPENDED'
        establishment.save()
        
        serializer = self.get_serializer(establishment)
        return Response({
            'success': True,
            'message': 'Establecimiento suspendido',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activa un establecimiento."""
        establishment = self.get_object()
        establishment.subscription_status = 'ACTIVE'
        establishment.is_active = True
        establishment.save()
        
        serializer = self.get_serializer(establishment)
        return Response({
            'success': True,
            'message': 'Establecimiento activado',
            'data': serializer.data
        })


class AdminThemeViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de temas de establecimientos."""
    permission_classes = [IsSuperAdmin]
    queryset = EstablishmentTheme.objects.all()
    serializer_class = EstablishmentThemeSerializer
    
    @action(detail=False, methods=['get'])
    def by_establishment(self, request):
        """Obtiene tema por ID de establecimiento."""
        establishment_id = request.query_params.get('establishment_id')
        if not establishment_id:
            return Response(
                {'error': 'establishment_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            theme = EstablishmentTheme.objects.get(establishment_id=establishment_id)
            serializer = self.get_serializer(theme)
            return Response(serializer.data)
        except EstablishmentTheme.DoesNotExist:
            return Response(
                {'error': 'Tema no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class CurrentUserViewSet(viewsets.ViewSet):
    """ViewSet para obtener información del usuario actual."""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtiene información del usuario autenticado."""
        serializer = UserSerializer(request.user)
        data = serializer.data
        
        establishment = None
        
        # Buscar establecimiento: primero como admin, luego en el perfil
        if hasattr(request.user, 'establishment_admin'):
            establishment = request.user.establishment_admin
        elif hasattr(request.user, 'profile') and request.user.profile.establishment:
            establishment = request.user.profile.establishment
        
        # Agregar información del establecimiento si existe
        if establishment:
            data['establishment'] = {
                'id': establishment.id,
                'nombre': establishment.planta_fruticola,
                'exportadora': establishment.exportadora or '',
                'has_active_subscription': establishment.has_active_subscription(),
                'subscription_expiry': establishment.subscription_expiry,
                'days_until_expiry': establishment.days_until_expiry()
            }
            
            # Agregar tema si existe
            if hasattr(establishment, 'theme'):
                data['establishment']['theme'] = EstablishmentThemeSerializer(
                    establishment.theme
                ).data
        
        return Response(data)
