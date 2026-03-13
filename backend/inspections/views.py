"""
Vistas para la API REST.
"""
import json
from rest_framework import viewsets, status, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Establishment, Inspection, SamplingResult, EstablishmentTheme
from .serializers import (
    EstablishmentSerializer,
    InspectionSerializer,
    SamplingResultSerializer,
    GenerarMuestreoSerializer
)
from .serializers_admin import EstablishmentThemeSerializer
from .utils import (
    calcular_muestreo,
    validate_stage_sampling,
    select_stage_sampling_pallets,
    distribute_samples_proportionally,
    generate_stage_sampling_numbers
)


class AllowAnyReadPermission(permissions.BasePermission):
    """
    Permite acceso anónimo para lectura (GET).
    Requiere autenticación para escritura (POST, PUT, DELETE).
    """
    def has_permission(self, request, view):
        # Permitir GET sin autenticación
        if request.method == 'GET':
            return True
        # Permitir POST sin autenticación también (para usuarios públicos generando muestreos)
        if request.method == 'POST':
            return True
        # Para otras operaciones, requerir autenticación
        return request.user and request.user.is_authenticated


class EstablishmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar establecimientos.
    Solo lectura desde el frontend. Acceso público.
    """
    queryset = Establishment.objects.filter(is_active=True)
    serializer_class = EstablishmentSerializer
    permission_classes = [AllowAnyReadPermission]


class InspectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar inspecciones.
    Acceso público.
    """
    queryset = Inspection.objects.all()
    serializer_class = InspectionSerializer
    permission_classes = [AllowAnyReadPermission]
    


class SamplingResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar resultados de muestreo.
    Solo lectura. Acceso público.
    """
    queryset = SamplingResult.objects.all()
    serializer_class = SamplingResultSerializer
    permission_classes = [AllowAnyReadPermission]


class MuestreoViewSet(viewsets.ViewSet):
    """
    ViewSet personalizado para generar muestreos.
    Acceso público para usuarios anónimos.
    """
    permission_classes = [AllowAnyReadPermission]
    
    @action(detail=False, methods=['post'], url_path='generar')
    def generar_muestreo(self, request):
        """
        Endpoint: POST /api/muestreo/generar/
        
        Crea una inspección y genera el muestreo automáticamente.
        
        Request Body:
        {
            "exportador": "string",
            "establecimiento_nombre": "string",
            "inspector_sag": "string",
            "contraparte_sag": "string",
            "especie": "string",
            "numero_lote": "string",
            "tamano_lote": int,
            "tipo_muestreo": "NORMAL|POR_ETAPA",
            "tipo_despacho": "string",
            "cantidad_pallets": int,
            "porcentaje_muestreo": float (opcional, default: 2.0)
        }
        
        Response:
        {
            "success": true,
            "message": "Muestreo generado exitosamente",
            "data": {
                "inspection": {...},
                "sampling_result": {
                    "tamano_lote": int,
                    "porcentaje_muestreo": float,
                    "tamano_muestra": int,
                    "cajas_seleccionadas": [int, int, ...]
                }
            }
        }
        """
        # Validar datos de entrada
        serializer = GenerarMuestreoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Datos inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            # Validaciones específicas para muestreo por etapa
            if data['tipo_muestreo'] == 'POR_ETAPA':
                boxes_per_pallet = data.get('boxes_per_pallet', [])
                
                if not boxes_per_pallet:
                    return Response({
                        'success': False,
                        'message': 'Debe especificar las cajas por pallet para muestreo por etapa'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Validar restricciones SAG/USDA
                es_valido, errores, warnings = validate_stage_sampling(
                    total_pallets=data['cantidad_pallets'],
                    boxes_per_pallet=boxes_per_pallet,
                    total_boxes_lot=data['tamano_lote']
                )
                
                if not es_valido:
                    return Response({
                        'success': False,
                        'message': 'Validación de muestreo por etapa fallida',
                        'errors': errores,
                        'warnings': warnings
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear la inspección
            inspection = Inspection.objects.create(
                exportador=data['exportador'],
                establecimiento_nombre=data['establecimiento_nombre'],
                establishment=None,  # Ya no se asocia obligatoriamente a un Establishment oficial
                inspector_sag=data['inspector_sag'],
                contraparte_sag=data['contraparte_sag'],
                especie=data['especie'],
                numero_lote=data['numero_lote'],
                tamano_lote=data['tamano_lote'],
                tipo_muestreo=data['tipo_muestreo'],
                tipo_despacho=data['tipo_despacho'],
                cantidad_pallets=data['cantidad_pallets'],
                boxes_per_pallet=data.get('boxes_per_pallet', [])
            )
            
            # Obtener incremento de intensidad (opcional)
            incremento_intensidad = data.get('incremento_intensidad', 0)
            
            # Calcular muestreo según el tipo
            if data['tipo_muestreo'] == 'POR_ETAPA':
                # Seleccionar pallets (25%)
                selected_pallets = select_stage_sampling_pallets(data['cantidad_pallets'])
                inspection.selected_pallets = selected_pallets
                inspection.save()
                
                # Calcular cajas totales SOLO de pallets seleccionados
                cajas_en_pallets_seleccionados = sum(
                    data['boxes_per_pallet'][i - 1] 
                    for i in selected_pallets
                )
                
                # Calcular tamaño de muestra basado SOLO en pallets seleccionados
                resultado_muestreo_base = calcular_muestreo(
                    tamano_lote=cajas_en_pallets_seleccionados,
                    especie=data['especie'],
                    incremento_intensidad=incremento_intensidad
                )
                
                # Distribuir muestras proporcionalmente entre pallets seleccionados
                sample_distribution = distribute_samples_proportionally(
                    boxes_per_pallet=data['boxes_per_pallet'],
                    selected_pallet_indices=selected_pallets,
                    total_sample_size=resultado_muestreo_base['tamano_muestra']
                )
                
                # Generar números aleatorios de cajas
                cajas_seleccionadas = generate_stage_sampling_numbers(
                    boxes_per_pallet=data['boxes_per_pallet'],
                    selected_pallet_indices=selected_pallets,
                    sample_distribution=sample_distribution
                )
                
                resultado_muestreo = {
                    'tamano_lote': data['tamano_lote'],  # Mantener el lote original para referencia
                    'tamano_lote_muestreado': cajas_en_pallets_seleccionados,  # Cajas realmente muestreadas
                    'tipo_tabla': resultado_muestreo_base['tipo_tabla'],
                    'nombre_tabla': resultado_muestreo_base['nombre_tabla'],
                    'muestra_base': resultado_muestreo_base['muestra_base'],
                    'incremento_aplicado': resultado_muestreo_base['incremento_aplicado'],
                    'muestra_final': resultado_muestreo_base['muestra_final'],
                    'tamano_muestra': len(cajas_seleccionadas),
                    'cajas_seleccionadas': cajas_seleccionadas,
                    'selected_pallets': selected_pallets,
                    'sample_distribution': sample_distribution
                }
            else:
                # Muestreo normal
                resultado_muestreo = calcular_muestreo(
                    tamano_lote=data['tamano_lote'],
                    especie=data['especie'],
                    incremento_intensidad=incremento_intensidad
                )
            
            # Guardar resultado del muestreo
            sampling_result = SamplingResult.objects.create(
                inspection=inspection,
                tipo_tabla=resultado_muestreo['tipo_tabla'],
                nombre_tabla=resultado_muestreo['nombre_tabla'],
                muestra_base=resultado_muestreo.get('muestra_base'),
                incremento_aplicado=resultado_muestreo.get('incremento_aplicado', 0),
                muestra_final=resultado_muestreo.get('muestra_final'),
                tamano_muestra=resultado_muestreo['tamano_muestra'],
                cajas_seleccionadas=json.dumps(resultado_muestreo['cajas_seleccionadas'])
            )
            
            # Preparar respuesta
            response_data = {
                'success': True,
                'message': 'Muestreo generado exitosamente',
                'data': {
                    'inspection': InspectionSerializer(inspection).data,
                    'sampling_result': {
                        'id': sampling_result.id,
                        'tamano_lote': resultado_muestreo['tamano_lote'],
                        'tipo_tabla': resultado_muestreo['tipo_tabla'],
                        'nombre_tabla': resultado_muestreo['nombre_tabla'],
                        'tamano_muestra': resultado_muestreo['tamano_muestra'],
                        'cajas_seleccionadas': resultado_muestreo['cajas_seleccionadas']
                    }
                }
            }
            
            # Agregar datos extra para muestreo por etapa
            if data['tipo_muestreo'] == 'POR_ETAPA':
                response_data['data']['sampling_result']['tamano_lote_muestreado'] = resultado_muestreo.get('tamano_lote_muestreado', resultado_muestreo['tamano_lote'])
                response_data['data']['stage_sampling'] = {
                    'selected_pallets': resultado_muestreo.get('selected_pallets', []),
                    'sample_distribution': resultado_muestreo.get('sample_distribution', {})
                }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al generar el muestreo',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='configurar-pallets/(?P<inspection_id>[^/.]+)')
    def configurar_pallets(self, request, inspection_id=None):
        """
        Endpoint: POST /api/muestreo/configurar-pallets/<inspection_id>/
        
        Guarda la configuración de base y altura para cada pallet.
        
        Request Body:
        {
            "configurations": [
                {"numero_pallet": 1, "base": 8, "cantidad_cajas": 120, "distribucion_caras": [4, 4]},
                {"numero_pallet": 2, "base": 6, "cantidad_cajas": 28, "distribucion_caras": [3, 3]},
                ...
            ]
        }
        
        Response:
        {
            "success": true,
            "message": "Configuraciones guardadas exitosamente"
        }
        """
        try:
            inspection = get_object_or_404(Inspection, id=inspection_id)
            
            configurations = request.data.get('configurations', [])
            
            if not configurations:
                return Response({
                    'success': False,
                    'message': 'Debe proporcionar configuraciones de pallets'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar que el número de configuraciones coincida con cantidad de pallets
            pallets_a_configurar = set()
            if inspection.tipo_muestreo == 'POR_ETAPA':
                # Solo pallets seleccionados
                pallets_a_configurar = set(inspection.selected_pallets)
            else:
                # Todos los pallets
                pallets_a_configurar = set(range(1, inspection.cantidad_pallets + 1))
            
            config_pallets = set(c.get('numero_pallet') for c in configurations)
            
            if config_pallets != pallets_a_configurar:
                return Response({
                    'success': False,
                    'message': f'Las configuraciones deben incluir exactamente los pallets: {sorted(pallets_a_configurar)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar y procesar cada configuración
            import math
            processed_configs = []
            for config in configurations:
                if 'numero_pallet' not in config or 'base' not in config or 'cantidad_cajas' not in config:
                    return Response({
                        'success': False,
                        'message': 'Cada configuración debe tener numero_pallet, base y cantidad_cajas'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                base = config['base']
                cantidad_cajas = config['cantidad_cajas']
                distribucion_caras = config.get('distribucion_caras', [])
                
                if base < 1 or cantidad_cajas < 1:
                    return Response({
                        'success': False,
                        'message': 'Base y cantidad de cajas deben ser mayores a 0'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Validar distribución de caras si se proporciona
                if distribucion_caras:
                    suma_caras = sum(distribucion_caras)
                    if suma_caras != base:
                        return Response({
                            'success': False,
                            'message': f'La suma de la distribución de caras ({suma_caras}) debe coincidir con la base ({base}) en el pallet {config["numero_pallet"]}'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calcular altura (capas) basándose en base y cantidad de cajas
                altura = math.ceil(cantidad_cajas / base)
                
                processed_configs.append({
                    'numero_pallet': config['numero_pallet'],
                    'base': base,
                    'cantidad_cajas': cantidad_cajas,
                    'altura': altura,
                    'distribucion_caras': distribucion_caras
                })
            
            # Guardar configuraciones procesadas
            inspection.pallet_configurations = processed_configs
            inspection.save()
            
            return Response({
                'success': True,
                'message': 'Configuraciones guardadas exitosamente',
                'data': {
                    'configurations': processed_configs
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al guardar configuraciones',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='diagrama-pallets/(?P<inspection_id>[^/.]+)')
    def get_diagrama_pallets(self, request, inspection_id=None):
        """
        Endpoint: GET /api/muestreo/diagrama-pallets/<inspection_id>/
        
        Retorna los datos necesarios para generar los diagramas de pallets.
        
        Response:
        {
            "success": true,
            "data": {
                "inspection": {...},
                "base_pallet": int,
                "altura_pallet": int,
                "cajas_por_pallet": int,
                "pallets": [
                    {
                        "numero_pallet": int,
                        "inicio_caja": int,
                        "fin_caja": int,
                        "cajas": [
                            {"numero": int, "capa": int, "seleccionada": bool},
                            ...
                        ],
                        "cajas_muestra": [int, int, ...]
                    },
                    ...
                ]
            }
        }
        """
        try:
            # Obtener inspección
            inspection = get_object_or_404(Inspection, id=inspection_id)
            
            # Verificar que tenga sampling_result
            if not hasattr(inspection, 'sampling_result'):
                return Response({
                    'success': False,
                    'message': 'La inspección no tiene resultados de muestreo'
                }, status=status.HTTP_404_NOT_FOUND)
            
            sampling_result = inspection.sampling_result
            
            # Verificar que tenga configuraciones de pallets
            if not inspection.pallet_configurations:
                return Response({
                    'success': False,
                    'message': 'Configuración de pallets requerida',
                    'requires_configuration': True
                }, status=status.HTTP_200_OK)
            
            # Obtener lista de cajas muestra
            cajas_seleccionadas = json.loads(sampling_result.cajas_seleccionadas)
            cajas_muestra_set = set(cajas_seleccionadas)
            
            # Convertir configuraciones a dict para acceso rápido
            config_dict = {c['numero_pallet']: c for c in inspection.pallet_configurations}
            
            # Determinar qué pallets mostrar
            if inspection.tipo_muestreo == 'POR_ETAPA':
                # Solo pallets seleccionados
                pallets_a_mostrar = inspection.selected_pallets
            else:
                # Todos los pallets (o los que tengan configuración)
                pallets_a_mostrar = [c['numero_pallet'] for c in inspection.pallet_configurations]
            
            # Generar datos para cada pallet
            pallets_data = []
            for num_pallet in sorted(pallets_a_mostrar):
                # Obtener configuración de este pallet
                if num_pallet not in config_dict:
                    continue
                
                config = config_dict[num_pallet]
                base = config['base']
                altura = config['altura']
                cantidad_cajas = config['cantidad_cajas']
                distribucion_caras = config.get('distribucion_caras', [])
                
                # Calcular rango de cajas de este pallet usando cantidad_cajas
                # Para POR_ETAPA: solo considerar pallets seleccionados anteriores
                # Para NORMAL: considerar todos los pallets anteriores
                inicio_caja = 1
                
                if inspection.tipo_muestreo == 'POR_ETAPA':
                    # Solo sumar cajas de pallets seleccionados anteriores
                    for pallet_anterior in sorted(pallets_a_mostrar):
                        if pallet_anterior >= num_pallet:
                            break
                        if pallet_anterior in config_dict:
                            inicio_caja += config_dict[pallet_anterior]['cantidad_cajas']
                else:
                    # Sumar cajas de todos los pallets anteriores
                    for i in range(1, num_pallet):
                        if i in config_dict:
                            inicio_caja += config_dict[i]['cantidad_cajas']
                
                fin_caja = inicio_caja + cantidad_cajas - 1
                
                # Filtrar cajas muestra de este pallet
                cajas_muestra_pallet = [c for c in cajas_seleccionadas if inicio_caja <= c <= fin_caja]
                
                # Generar estructura de cajas con su información
                cajas = []
                for num_caja_global in range(inicio_caja, fin_caja + 1):
                    # Número de caja dentro del pallet (1-based)
                    num_caja_local = num_caja_global - inicio_caja + 1
                    
                    # Calcular capa (1-based)
                    import math
                    capa = math.ceil(num_caja_local / base)
                    
                    cajas.append({
                        'numero': num_caja_global,
                        'numero_local': num_caja_local,
                        'capa': capa,
                        'seleccionada': num_caja_global in cajas_muestra_set
                    })
                
                pallets_data.append({
                    'numero_pallet': num_pallet,
                    'base': base,
                    'altura': altura,
                    'cantidad_cajas': cantidad_cajas,
                    'distribucion_caras': distribucion_caras,
                    'inicio_caja': inicio_caja,
                    'fin_caja': fin_caja,
                    'cajas': cajas,
                    'cajas_muestra': cajas_muestra_pallet,
                    'total_cajas_muestra': len(cajas_muestra_pallet)
                })
            
            return Response({
                'success': True,
                'data': {
                    'inspection': InspectionSerializer(inspection).data,
                    'total_pallets_mostrados': len(pallets_data),
                    'pallets': pallets_data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener diagrama de pallets',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ThemeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet público para que los establecimientos obtengan su tema.
    Solo lectura. Acceso público.
    """
    queryset = EstablishmentTheme.objects.all()
    serializer_class = EstablishmentThemeSerializer
    permission_classes = [AllowAnyReadPermission]
    
    @action(detail=False, methods=['get'], url_path='my-theme')
    def my_theme(self, request):
        """
        Endpoint: GET /api/themes/my-theme/
        
        Retorna el tema del establecimiento del usuario autenticado.
        """
        if not request.user.is_authenticated:
            return Response({
                'error': 'Usuario no autenticado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Obtener establecimiento del usuario
        establishment = None
        if hasattr(request.user, 'establishment_admin'):
            establishment = request.user.establishment_admin
        
        if not establishment:
            return Response({
                'error': 'Usuario no tiene un establecimiento asociado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener o crear tema
        theme, created = EstablishmentTheme.objects.get_or_create(
            establishment=establishment
        )
        
        serializer = self.get_serializer(theme)
        return Response(serializer.data)
