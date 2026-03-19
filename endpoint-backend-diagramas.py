"""
============================================================================
ENDPOINT BACKEND DJANGO REST FRAMEWORK
============================================================================

Para que el frontend pueda generar el PDF, necesitas este endpoint en tu backend.

UBICACIÓN: backend/inspections/views.py
RUTA: GET /api/muestreo/diagrama-pallets/{inspection_id}/

"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Inspection
import math

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pallet_diagrams(request, inspection_id):
    """
    GET /api/muestreo/diagrama-pallets/{inspection_id}/
    
    Obtiene datos formateados para generar diagramas PDF de pallets
    
    Response Success:
    {
      success: true,
      requires_configuration: false,
      data: {
        inspection: {...},
        total_pallets_mostrados: 5,
        pallets: [...]
      }
    }
    
    Response Error (Sin configuración):
    {
      success: false,
      requires_configuration: true,
      message: "Se requiere configuración de pallets"
    }
    """
    try:
        inspection = Inspection.objects.get(id=inspection_id)
        
        # 1. VALIDAR QUE ESTÉ CONFIGURADO
        if not inspection.pallet_configurations or len(inspection.pallet_configurations) == 0:
            return Response({
                'success': False,
                'requires_configuration': True,
                'message': 'Se requiere configuración de pallets'
            }, status=400)
        
        # 2. OBTENER DATOS DEL MUESTREO
        sampled_numbers = inspection.sampled_numbers or []  # Números de cajas muestreadas
        
        # 3. CONSTRUIR DATOS DE PALLETS
        pallets_data = []
        offset = 0  # Para numeración continua
        
        # ========== LÓGICA: Determinar qué pallets mostrar ==========
        if inspection.tipo_muestreo == 'POR_ETAPA':
            # Solo pallets seleccionados
            pallets_to_show = inspection.selected_pallets or []
        else:
            # Todos los pallets
            pallets_to_show = list(range(1, inspection.cantidad_pallets + 1))
        
        # ========== LOOP: Procesar cada pallet ==========
        for pallet_number in pallets_to_show:
            # Obtener configuración del pallet
            config = None
            for cfg in inspection.pallet_configurations:
                if cfg.get('numero_pallet') == pallet_number:
                    config = cfg
                    break
            
            if not config:
                continue  # Skip si no tiene configuración
            
            # ========== EXTRAER CONFIGURACIÓN ==========
            base = config.get('base', 0)
            cantidad_cajas = config.get('cantidad_cajas', 0)
            distribucion_caras = config.get('distribucion_caras', [])
            
            if base <= 0 or cantidad_cajas <= 0:
                continue
            
            # ========== CALCULAR CAPAS ==========
            altura = math.ceil(cantidad_cajas / base)
            
            # ========== CALCULAR RANGO DE CAJAS PARA ESTE PALLET ==========
            inicio_caja = offset + 1
            fin_caja = offset + cantidad_cajas
            offset = fin_caja
            
            # ========== CONTAR MUESTRAS EN ESTE PALLET ==========
            total_cajas_muestra = sum(
                1 for num in sampled_numbers 
                if inicio_caja <= num <= fin_caja
            )
            
            # ========== CONSTRUIR ARRAY DE CAJAS ==========
            cajas = []
            for numero_local in range(1, cantidad_cajas + 1):
                numero_global = inicio_caja + numero_local - 1
                
                # Calcular capa (desde abajo = 1)
                capa = math.ceil(numero_local / base)
                
                # ¿Es muestra?
                es_muestra = numero_global in sampled_numbers
                
                cajas.append({
                    'numero': numero_global,           # Número global correlativo
                    'numero_local': numero_local,      # Posición en grilla (1 a base*altura)
                    'capa': capa,                      # Capa (1 = abajo, altura = arriba)
                    'seleccionada': es_muestra         # ¿Es muestra?
                })
            
            # ========== CONSTRUIR PALLET ==========
            pallet_data = {
                'numero_pallet': pallet_number,
                'base': base,
                'altura': altura,
                'cantidad_cajas': cantidad_cajas,
                'distribucion_caras': distribucion_caras,
                'inicio_caja': inicio_caja,
                'fin_caja': fin_caja,
                'total_cajas_muestra': total_cajas_muestra,
                'cajas': cajas
            }
            
            pallets_data.append(pallet_data)
        
        # 4. RETORNAR RESPUESTA
        return Response({
            'success': True,
            'requires_configuration': False,
            'data': {
                'inspection': {
                    'id': inspection.id,
                    'numero_lote': inspection.numero_lote,
                    'especie': inspection.especie,
                    'tipo_muestreo': inspection.tipo_muestreo,
                    'cantidad_pallets': inspection.cantidad_pallets
                },
                'total_pallets_mostrados': len(pallets_data),
                'pallets': pallets_data
            }
        })
    
    except Inspection.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Inspección no encontrada'
        }, status=404)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)


"""
============================================================================
REGISTRAR EN urls.py
============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # ... otros endpoints ...
    path('diagrama-pallets/<int:inspection_id>/', views.get_pallet_diagrams, name='get-pallet-diagrams'),
]
"""


"""
============================================================================
ESTRUCTURA DE DATOS: pallet_configurations (en modelo Inspection)
============================================================================

Este es un JSONField que debe contener:

[
  {
    "numero_pallet": 1,
    "base": 8,                      # Cajas por capa
    "cantidad_cajas": 28,           # Total cajas en pallet
    "distribucion_caras": [4, 4],   # Columnas por cara
    "distribucion_personalizada": false
  },
  {
    "numero_pallet": 2,
    "base": 8,
    "cantidad_cajas": 28,
    "distribucion_caras": [4, 4],
    "distribucion_personalizada": false
  }
]

Se guarda mediante el endpoint POST /api/muestreo/configurar-pallets/{id}/
que ya existe en tu proyecto.
"""


"""
============================================================================
EJEMPLO DE RESPUESTA COMPLETA
============================================================================
"""

response_example = {
    "success": True,
    "requires_configuration": False,
    "data": {
        "inspection": {
            "id": 123,
            "numero_lote": "LOTE-2024-001",
            "especie": "Mango",
            "tipo_muestreo": "ALEATORIO",
            "cantidad_pallets": 5
        },
        "total_pallets_mostrados": 3,
        "pallets": [
            {
                "numero_pallet": 1,
                "base": 8,
                "altura": 4,
                "cantidad_cajas": 28,
                "distribucion_caras": [4, 4],
                "inicio_caja": 1,
                "fin_caja": 28,
                "total_cajas_muestra": 4,
                "cajas": [
                    {
                        "numero": 1,
                        "numero_local": 1,
                        "capa": 1,
                        "seleccionada": True
                    },
                    {
                        "numero": 2,
                        "numero_local": 2,
                        "capa": 1,
                        "seleccionada": False
                    },
                    # ... cajas 3-28
                ]
            },
            {
                "numero_pallet": 2,
                "base": 8,
                "altura": 4,
                "cantidad_cajas": 28,
                "distribucion_caras": [4, 4],
                "inicio_caja": 29,
                "fin_caja": 56,
                "total_cajas_muestra": 3,
                "cajas": [...]
            },
            {
                "numero_pallet": 3,
                "base": 6,
                "altura": 5,
                "cantidad_cajas": 28,
                "distribucion_caras": [3, 3],
                "inicio_caja": 57,
                "fin_caja": 84,
                "total_cajas_muestra": 2,
                "cajas": [...]
            }
        ]
    }
}

"""
============================================================================
FLUJO LÓGICO DETALLADO
============================================================================

1. Backend obtiene Inspection
   └─ Valida que pallet_configurations existe

2. Backend obtiene sampled_numbers
   └─ Array de números globales de cajas muestreadas

3. Para cada pallet seleccionado:
   
   a) Obtener configuración (base, altura, distribucion_caras)
   
   b) Calcular rangos (inicio_caja, fin_caja)
      ├─ Pallet 1: 1 - 28
      ├─ Pallet 2: 29 - 56
      └─ Pallet 3: 57 - 84
      
      Nota: La numeración es CONTINUA si es POR_ETAPA,
            pero si es ALEATORIO podría ser diferente
   
   c) Contar muestras en rango
      └─ Si numero ∈ [inicio, fin] y numero ∈ sampled_numbers
         entonces es_muestra = true
   
   d) Para cada caja del pallet:
      ├─ numero = global
      ├─ numero_local = posición en grilla (1 a base*altura)
      ├─ capa = Math.ceil(numero_local / base)
      └─ seleccionada = true/false

4. Frontend recibe estructura y renderiza diagramas

"""


"""
============================================================================
VALIDACIONES IMPORTANTES
============================================================================

1. pallet_configurations debe tener todos los pallets a mostrar
   ├─ Si falta uno → skip ese pallet
   └─ Si está vacío → retornar requires_configuration = true

2. base y cantidad_cajas deben ser > 0
   └─ Si no → skip ese pallet

3. sampled_numbers debe ser un array de números enteros
   └─ Si no existe → todos los valores de seleccionada = false

4. La suma de distribucion_caras debe igualar base
   └─ Frontend lo valida, backend lo recibe ya validado

5. En POR_ETAPA: los pallets son contiguos en numeración
   └─ Pallet 3: cajas 1-120
   └─ Pallet 5: cajas 121-240
   (VER generate_stage_sampling_numbers en utils.py)

"""
