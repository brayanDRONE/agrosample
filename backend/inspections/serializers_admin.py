"""
Serializers para el panel de administración.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import Establishment, EstablishmentTheme, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para perfil de usuario."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'avatar', 'sample_label_text', 'created_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer para usuario."""
    profile = UserProfileSerializer(read_only=True)
    role = serializers.SerializerMethodField()
    is_superadmin = serializers.SerializerMethodField()
    is_establishment_admin = serializers.SerializerMethodField()
    sample_label_text = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'is_active', 'profile', 'role', 
            'is_superadmin', 'is_establishment_admin', 'sample_label_text'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }
    
    def get_role(self, obj):
        """Obtiene el rol del perfil del usuario."""
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return None
    
    def get_is_superadmin(self, obj):
        """Verifica si el usuario es superadmin."""
        if hasattr(obj, 'profile'):
            return obj.profile.is_superadmin()
        return False
    
    def get_is_establishment_admin(self, obj):
        """Verifica si el usuario es admin de establecimiento."""
        if hasattr(obj, 'profile'):
            return obj.profile.is_establishment_admin()
        return False

    def get_sample_label_text(self, obj):
        """Obtiene texto personalizado para etiquetas de muestra."""
        if hasattr(obj, 'profile') and obj.profile.sample_label_text:
            return obj.profile.sample_label_text
        return 'MUESTRA USDA'


class EstablishmentThemeSerializer(serializers.ModelSerializer):
    """Serializer para tema de establecimiento."""
    
    class Meta:
        model = EstablishmentTheme
        fields = [
            'id', 'primary_color', 'secondary_color', 'accent_color',
            'logo', 'logo_dark', 'favicon', 'company_name',
            'welcome_message', 'footer_text', 'show_logo', 'dark_mode'
        ]


class EstablishmentDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para establecimiento (admin)."""
    admin_user_details = UserSerializer(source='admin_user', read_only=True)
    theme = EstablishmentThemeSerializer(read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    is_expiring_soon = serializers.SerializerMethodField()
    has_active_subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = Establishment
        fields = [
            'id', 'exportadora', 'planta_fruticola', 'rut', 
            'address', 'phone', 'email', 'encargado_sag',
            'admin_user', 'admin_user_details', 'is_active',
            'subscription_status', 'subscription_start', 'subscription_expiry',
            'license_key', 'sample_label_text', 'created_at', 'updated_at',
            'theme', 'days_until_expiry', 'is_expiring_soon',
            'has_active_subscription'
        ]
        read_only_fields = ['created_at', 'updated_at', 'license_key']
    
    def get_days_until_expiry(self, obj):
        """Calcula días hasta expiración y actualiza estado si es necesario."""
        from django.utils import timezone
        
        days = obj.days_until_expiry()
        
        # Si no hay fecha de expiración, retornar 0
        if days is None:
            return 0
        
        # Si ya expiró y está marcado como ACTIVE, actualizar a EXPIRED
        if days <= 0 and obj.subscription_status == 'ACTIVE':
            obj.subscription_status = 'EXPIRED'
            obj.save(update_fields=['subscription_status'])
            return 0
        
        # Retornar 0 si es negativo (por si acaso)
        if days < 0:
            return 0
            
        return days
    
    def get_is_expiring_soon(self, obj):
        return obj.is_expiring_soon()
    
    def get_has_active_subscription(self, obj):
        return obj.has_active_subscription()


class EstablishmentCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear establecimiento con usuario."""
    # Datos del usuario administrador
    admin_username = serializers.CharField(write_only=True)
    admin_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    admin_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    admin_first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    admin_last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    subscription_days = serializers.IntegerField(write_only=True, default=30, min_value=1)
    
    class Meta:
        model = Establishment
        fields = [
            'exportadora', 'planta_fruticola', 'rut', 
            'address', 'phone', 'email', 'encargado_sag',
            'sample_label_text',
            'admin_username', 'admin_password', 'admin_email',
            'admin_first_name', 'admin_last_name', 'subscription_days'
        ]
    
    def create(self, validated_data):
        from django.utils import timezone
        from datetime import timedelta
        
        # Extraer datos del usuario
        admin_username = validated_data.pop('admin_username')
        admin_password = validated_data.pop('admin_password')
        admin_email = validated_data.pop('admin_email')
        admin_first_name = validated_data.pop('admin_first_name', '')
        admin_last_name = validated_data.pop('admin_last_name', '')
        subscription_days = validated_data.pop('subscription_days', 30)
        
        # Obtener texto de etiqueta (desde sample_label_text del establecimiento)
        sample_label_text = validated_data.get('sample_label_text', 'MUESTRA USDA')
        
        # Crear usuario
        admin_user = User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name=admin_first_name,
            last_name=admin_last_name
        )
        
        # Generar license key
        import uuid
        license_key = f"EST-{uuid.uuid4().hex[:12].upper()}"
        
        # Calcular fecha de expiración
        today = timezone.now().date()
        subscription_expiry = today + timedelta(days=subscription_days)
        subscription_start = today
        
        # Asegurar que subscription_status sea ACTIVE
        validated_data['subscription_status'] = 'ACTIVE'
        validated_data['subscription_start'] = subscription_start
        validated_data['subscription_expiry'] = subscription_expiry
        
        # Crear establecimiento
        establishment = Establishment.objects.create(
            admin_user=admin_user,
            license_key=license_key,
            created_by=self.context['request'].user,
            **validated_data
        )
        
        # Crear perfil con rol de administrador de establecimiento
        # y asignar el establecimiento
        UserProfile.objects.create(
            user=admin_user,
            role='ESTABLISHMENT_ADMIN',
            establishment=establishment,
            sample_label_text=sample_label_text
        )
        
        # Crear tema por defecto
        EstablishmentTheme.objects.create(establishment=establishment)
        
        return establishment


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del dashboard."""
    total_establishments = serializers.IntegerField()
    active_establishments = serializers.IntegerField()
    expiring_soon = serializers.IntegerField()
    expired_establishments = serializers.IntegerField()
    total_inspections = serializers.IntegerField()
    inspections_this_month = serializers.IntegerField()
