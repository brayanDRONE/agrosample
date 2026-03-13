"""
Modelos para el sistema de inspecciones SAG-USDA.
"""
from django.db import models
from django.db.models import JSONField
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User


def get_current_date():
    """Retorna la fecha actual."""
    return timezone.now().date()


def get_current_time():
    """Retorna la hora actual."""
    return timezone.now().time()


class Establishment(models.Model):
    """
    Modelo para establecimientos/plantas.
    Controla el acceso mediante suscripción mensual.
    """
    SUBSCRIPTION_STATUS_CHOICES = [
        ('ACTIVE', 'Activa'),
        ('EXPIRED', 'Expirada'),
        ('SUSPENDED', 'Suspendida'),
    ]
    
    # Información básica
    exportadora = models.CharField(max_length=255, null=True, blank=True, verbose_name='Exportadora')
    planta_fruticola = models.CharField(max_length=255, default='Sin nombre', verbose_name='Planta Frutícola')
    rut = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='RUT')
    address = models.TextField(null=True, blank=True, verbose_name='Dirección')
    phone = models.CharField(max_length=50, null=True, blank=True, verbose_name='Teléfono')
    email = models.EmailField(null=True, blank=True, verbose_name='Email de Contacto')
    encargado_sag = models.CharField(max_length=255, null=True, blank=True, verbose_name='Encargado Área SAG')
    
    # Usuario administrador del establecimiento
    admin_user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='establishment_admin',
        verbose_name='Usuario Administrador'
    )
    
    # Control de acceso
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='ACTIVE',
        verbose_name='Estado de Suscripción'
    )
    subscription_start = models.DateField(
        null=True,
        blank=True,
        verbose_name='Inicio de Suscripción'
    )
    subscription_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Expiración'
    )
    license_key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Clave de Licencia'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='establishments_created',
        verbose_name='Creado Por'
    )
    
    class Meta:
        verbose_name = 'Establecimiento'
        verbose_name_plural = 'Establecimientos'
        ordering = ['planta_fruticola']
    
    def __str__(self):
        return self.planta_fruticola or 'Sin nombre'
    
    def has_active_subscription(self):
        """Verifica si la suscripción está activa."""
        if self.subscription_status != 'ACTIVE':
            return False
        if self.subscription_expiry and self.subscription_expiry < timezone.now().date():
            return False
        return True
    
    def days_until_expiry(self):
        """Calcula días hasta que expire la suscripción."""
        if not self.subscription_expiry:
            return None
        today = timezone.now().date()
        delta = self.subscription_expiry - today
        return delta.days
    
    def is_expiring_soon(self, days=7):
        """Verifica si la suscripción está por vencer."""
        days_left = self.days_until_expiry()
        if days_left is None:
            return False
        return 0 < days_left <= days


class Inspection(models.Model):
    """
    Modelo para inspecciones realizadas.
    """
    SAMPLING_TYPE_CHOICES = [
        ('NORMAL', 'Normal'),
        ('POR_ETAPA', 'Por Etapa'),
    ]
    
    # Información general
    exportador = models.CharField(max_length=255, verbose_name='Exportador')
    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.CASCADE,
        related_name='inspections',
        verbose_name='Planta/Establecimiento (Referencia)',
        null=True,
        blank=True
    )
    establecimiento_nombre = models.CharField(
        max_length=255, 
        verbose_name='Planta/Establecimiento',
        null=True,
        blank=True
    )
    inspector_sag = models.CharField(max_length=255, verbose_name='Inspector SAG')
    contraparte_sag = models.CharField(max_length=255, verbose_name='Contraparte SAG')
    
    # Fecha y hora (automáticas)
    fecha = models.DateField(default=get_current_date, verbose_name='Fecha')
    hora = models.TimeField(default=get_current_time, verbose_name='Hora')
    
    # Detalles del lote
    especie = models.CharField(max_length=100, verbose_name='Especie')
    numero_lote = models.CharField(max_length=100, verbose_name='Número de Lote')
    tamano_lote = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Tamaño del Lote'
    )
    tipo_muestreo = models.CharField(
        max_length=20,
        choices=SAMPLING_TYPE_CHOICES,
        default='NORMAL',
        verbose_name='Tipo de Muestreo'
    )
    tipo_despacho = models.CharField(max_length=100, verbose_name='Tipo de Despacho')
    cantidad_pallets = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad de Pallets'
    )
    
    # Configuración de pallets para diagramas (por pallet individual)
    pallet_configurations = JSONField(
        default=list,
        blank=True,
        verbose_name='Configuraciones de Pallets',
        help_text='Array con configuración de cada pallet: [{numero_pallet, base, altura}, ...]'
    )
    
    # Muestreo por etapa - Cajas por pallet
    boxes_per_pallet = JSONField(
        default=list,
        blank=True,
        verbose_name='Cajas por Pallet',
        help_text='Array con cantidad de cajas en cada pallet (solo para muestreo por etapa)'
    )
    selected_pallets = JSONField(
        default=list,
        blank=True,
        verbose_name='Pallets Seleccionados',
        help_text='Índices de pallets seleccionados para muestreo (solo para muestreo por etapa)'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Inspección'
        verbose_name_plural = 'Inspecciones'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Inspección {self.numero_lote} - {self.exportador}"


class SamplingResult(models.Model):
    """
    Modelo para almacenar los resultados del muestreo.
    """
    inspection = models.OneToOneField(
        Inspection,
        on_delete=models.CASCADE,
        related_name='sampling_result',
        verbose_name='Inspección'
    )
    
    # Parámetros del muestreo
    porcentaje_muestreo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.00,
        verbose_name='Porcentaje de Muestreo',
        null=True,
        blank=True
    )
    
    # Tipo de tabla de muestreo utilizada
    tipo_tabla = models.CharField(
        max_length=50,
        verbose_name='Tipo de Tabla',
        null=True,
        blank=True
    )
    
    # Nombre descriptivo de la tabla
    nombre_tabla = models.CharField(
        max_length=100,
        verbose_name='Nombre de Tabla',
        default='Hipergeométrica del 6%'
    )
    
    # Incremento de intensidad de muestreo (opcional)
    muestra_base = models.IntegerField(
        verbose_name='Muestra Base',
        null=True,
        blank=True,
        help_text='Tamaño de muestra antes del incremento'
    )
    incremento_aplicado = models.IntegerField(
        verbose_name='Incremento Aplicado (%)',
        default=0,
        help_text='Incremento de intensidad: 0, 20 o 40'
    )
    muestra_final = models.IntegerField(
        verbose_name='Muestra Final',
        null=True,
        blank=True,
        help_text='Tamaño de muestra después del incremento'
    )
    
    # Mantener compatibilidad - tamano_muestra apunta a muestra_final
    tamano_muestra = models.IntegerField(verbose_name='Tamaño de la Muestra')
    
    # Resultados (almacenados como JSON en texto)
    cajas_seleccionadas = models.TextField(verbose_name='Cajas Seleccionadas')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Resultado de Muestreo'
        verbose_name_plural = 'Resultados de Muestreo'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Muestreo para {self.inspection.numero_lote}"
    
    def get_cajas_list(self):
        """Convierte el string de cajas en lista de enteros."""
        import json
        return json.loads(self.cajas_seleccionadas)


class EstablishmentTheme(models.Model):
    """
    Modelo para personalización visual de establecimientos.
    Permite al superadmin personalizar la interfaz de cada establecimiento.
    """
    establishment = models.OneToOneField(
        Establishment,
        on_delete=models.CASCADE,
        related_name='theme',
        verbose_name='Establecimiento'
    )
    
    # Colores
    primary_color = models.CharField(
        max_length=7,
        default='#2563eb',
        verbose_name='Color Primario',
        help_text='Formato hexadecimal: #RRGGBB'
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#6b7280',
        verbose_name='Color Secundario',
        help_text='Formato hexadecimal: #RRGGBB'
    )
    accent_color = models.CharField(
        max_length=7,
        default='#10b981',
        verbose_name='Color de Acento',
        help_text='Formato hexadecimal: #RRGGBB'
    )
    
    # Logos y imágenes
    logo = models.ImageField(
        upload_to='logos/',
        null=True,
        blank=True,
        verbose_name='Logo'
    )
    logo_dark = models.ImageField(
        upload_to='logos/',
        null=True,
        blank=True,
        verbose_name='Logo (Versión Oscura)'
    )
    favicon = models.ImageField(
        upload_to='favicons/',
        null=True,
        blank=True,
        verbose_name='Favicon'
    )
    
    # Textos personalizados
    company_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Nombre de Empresa (Mostrar)'
    )
    welcome_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mensaje de Bienvenida'
    )
    footer_text = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Texto del Footer'
    )
    
    # Configuraciones visuales
    show_logo = models.BooleanField(default=True, verbose_name='Mostrar Logo')
    dark_mode = models.BooleanField(default=False, verbose_name='Modo Oscuro por Defecto')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tema de Establecimiento'
        verbose_name_plural = 'Temas de Establecimientos'
    
    def __str__(self):
        return f"Tema de {self.establishment.planta_fruticola or 'Sin nombre'}"


class UserProfile(models.Model):
    """
    Perfil de usuario extendido.
    """
    USER_ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Administrador'),
        ('ESTABLISHMENT_ADMIN', 'Administrador de Establecimiento'),
        ('INSPECTOR', 'Inspector'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario'
    )
    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members',
        verbose_name='Establecimiento Asignado',
        help_text='Establecimiento al que pertenece este usuario (para inspectores y admins)'
    )
    role = models.CharField(
        max_length=30,
        choices=USER_ROLE_CHOICES,
        default='INSPECTOR',
        verbose_name='Rol'
    )
    phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Teléfono'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Avatar'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_superadmin(self):
        return self.role == 'SUPERADMIN'
    
    def is_establishment_admin(self):
        return self.role == 'ESTABLISHMENT_ADMIN'
