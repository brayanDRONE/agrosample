"""
Serializers para la API REST.
"""
from rest_framework import serializers
from .models import Establishment, Inspection, SamplingResult


class EstablishmentSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Establishment.
    """
    has_active_subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = Establishment
        fields = [
            'id', 'planta_fruticola', 'exportadora', 'is_active', 'subscription_status',
            'subscription_expiry', 'has_active_subscription'
        ]
        read_only_fields = ['id']
    
    def get_has_active_subscription(self, obj):
        return obj.has_active_subscription()


class InspectionSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Inspection.
    """
    establishment_name = serializers.CharField(source='establishment.planta_fruticola', read_only=True)
    
    class Meta:
        model = Inspection
        fields = [
            'id', 'exportador', 'establishment', 'establecimiento_nombre', 'establishment_name',
            'inspector_sag', 'contraparte_sag', 'fecha', 'hora',
            'especie', 'numero_lote', 'tamano_lote', 'tipo_muestreo',
            'tipo_despacho', 'cantidad_pallets', 'pallet_configurations',
            'boxes_per_pallet', 'selected_pallets', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'fecha', 'hora', 'selected_pallets']
    
    def validate_tamano_lote(self, value):
        if value <= 0:
            raise serializers.ValidationError("El tamaño del lote debe ser mayor a 0")
        return value
    
    def validate_cantidad_pallets(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad de pallets debe ser mayor a 0")
        return value


class SamplingResultSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo SamplingResult.
    """
    cajas_list = serializers.SerializerMethodField()
    inspection_data = InspectionSerializer(source='inspection', read_only=True)
    
    class Meta:
        model = SamplingResult
        fields = [
            'id', 'inspection', 'inspection_data', 'porcentaje_muestreo',
            'tipo_tabla', 'nombre_tabla',
            'tamano_muestra', 'cajas_seleccionadas', 'cajas_list',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_cajas_list(self, obj):
        return obj.get_cajas_list()


class GenerarMuestreoSerializer(serializers.Serializer):
    """
    Serializer para el endpoint de generación de muestreo.
    """
    # Datos de la inspección
    exportador = serializers.CharField(max_length=255, required=False, allow_blank=True, default='N/A')
    establecimiento_nombre = serializers.CharField(max_length=255, required=False, allow_blank=True, default='N/A')
    inspector_sag = serializers.CharField(max_length=255, required=False, allow_blank=True, default='N/A')
    contraparte_sag = serializers.CharField(max_length=255, required=False, allow_blank=True, default='N/A')
    especie = serializers.CharField(max_length=100, required=False, allow_blank=True, default='N/A')
    numero_lote = serializers.CharField(max_length=100)
    tamano_lote = serializers.IntegerField(min_value=1, required=False)
    tipo_muestreo = serializers.ChoiceField(choices=['NORMAL', 'POR_ETAPA'], default='NORMAL', required=False)
    tipo_despacho = serializers.CharField(max_length=100, required=False, allow_blank=True, default='N/A')
    cantidad_pallets = serializers.IntegerField(min_value=1)

    # Modo manual: números definidos por el usuario (opcional en esta etapa)
    numeros_muestra_manual = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        default=list
    )
    
    # Para muestreo por etapa
    boxes_per_pallet = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True
    )
    
    # Parámetro opcional para porcentaje (default: 2%)
    porcentaje_muestreo = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.00,
        required=False
    )
    
    # Parámetro opcional para incremento de intensidad (0, 20, 40)
    incremento_intensidad = serializers.IntegerField(
        default=0,
        required=False,
        min_value=0,
        max_value=40
    )
    
    def validate_incremento_intensidad(self, value):
        """Valida que el incremento sea 0, 20 o 40."""
        if value not in [0, 20, 40]:
            raise serializers.ValidationError("El incremento debe ser 0, 20 o 40")
        return value

    def validate(self, attrs):
        """Completa valores por defecto para el flujo simplificado."""
        tamano_lote = attrs.get('tamano_lote')
        cantidad_pallets = attrs.get('cantidad_pallets')

        if not tamano_lote:
            attrs['tamano_lote'] = cantidad_pallets

        numeros = attrs.get('numeros_muestra_manual', [])
        attrs['numeros_muestra_manual'] = sorted(set(numeros))
        return attrs
