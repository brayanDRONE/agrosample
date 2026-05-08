"""
batch_description_views.py - Vistas API para el módulo de planilla de descripción
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
from datetime import datetime

from batch_description_utils import INSFileParser, validate_ins_file


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parse_ins_file(request):
    """
    Endpoint para parsear archivos .INS
    
    Expected POST request with file upload
    
    Returns:
        {
            "success": bool,
            "message": str,
            "data": {
                "header": {...},
                "pallets": [...],
                "total_pallets": int,
                "warnings": []
            },
            "errors": []
        }
    """
    try:
        # Verificar que se proporcionó un archivo
        if 'file' not in request.FILES:
            return Response(
                {
                    'success': False,
                    'message': 'No se proporcionó archivo',
                    'errors': ['No se encontró archivo en la solicitud']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Verificar extensión
        if not uploaded_file.name.lower().endswith('.ins'):
            return Response(
                {
                    'success': False,
                    'message': 'Formato de archivo inválido',
                    'errors': ['El archivo debe tener extensión .INS']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Leer contenido del archivo
        try:
            file_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            # Intentar con otra codificación
            try:
                file_content = uploaded_file.read().decode('latin-1')
            except:
                return Response(
                    {
                        'success': False,
                        'message': 'No se puede leer el archivo',
                        'errors': ['El archivo debe ser de texto UTF-8 o Latin-1']
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar estructura básica
        is_valid, error_msg = validate_ins_file(file_content)
        if not is_valid:
            return Response(
                {
                    'success': False,
                    'message': error_msg,
                    'errors': [error_msg]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parsear archivo
        parser = INSFileParser(file_content)
        parsed_data = parser.parse()
        
        if parser.errors:
            return Response(
                {
                    'success': False,
                    'message': 'Error al parsear el archivo',
                    'errors': parser.errors,
                    'warnings': parser.warnings
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Retornar datos parseados
        return Response(
            {
                'success': True,
                'message': 'Archivo procesado correctamente',
                'data': parsed_data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {
                'success': False,
                'message': 'Error interno del servidor',
                'errors': [str(e)]
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_batch_description(request):
    """
    Endpoint para generar la planilla de descripción de lote
    
    Expected POST data:
    {
        "inspection_type": "NORMAL" | "ETAPA",
        "batch_data": {...},
        "certificates": {
            "premuestre": [...],
            "inspeccion": [...]
        }
    }
    
    Returns:
        {
            "success": bool,
            "message": str,
            "data": {...},
            "errors": []
        }
    """
    try:
        data = request.data
        
        # Validar datos requeridos
        required_fields = ['inspection_type', 'batch_data', 'certificates']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return Response(
                {
                    'success': False,
                    'message': 'Datos incompletos',
                    'errors': [f'Falta el campo: {field}' for field in missing_fields]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inspection_type = data.get('inspection_type')
        if inspection_type not in ['NORMAL', 'ETAPA']:
            return Response(
                {
                    'success': False,
                    'message': 'Tipo de inspección inválido',
                    'errors': ['El tipo debe ser NORMAL o ETAPA']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aquí iría la lógica de generación de planilla
        # Por ahora, solo retornamos confirmación
        
        return Response(
            {
                'success': True,
                'message': 'Planilla generada correctamente',
                'data': {
                    'inspection_type': inspection_type,
                    'generated_at': datetime.now().isoformat(),
                    'status': 'ready_for_export'
                }
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {
                'success': False,
                'message': 'Error interno del servidor',
                'errors': [str(e)]
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_batch_description(request):
    """
    Endpoint para exportar la planilla en PDF o Excel
    
    Expected POST data:
    {
        "format": "pdf" | "excel",
        "batch_data": {...},
        "certificates": {...}
    }
    
    Returns:
        Archivo descargable
    """
    try:
        data = request.data
        format_type = data.get('format', 'pdf').lower()
        
        if format_type not in ['pdf', 'excel']:
            return Response(
                {
                    'success': False,
                    'message': 'Formato de exportación inválido',
                    'errors': ['El formato debe ser pdf o excel']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aquí iría la lógica de exportación
        # Por ahora, retornamos confirmación
        
        return Response(
            {
                'success': True,
                'message': f'Exportación a {format_type} lista',
                'data': {
                    'format': format_type,
                    'status': 'ready_for_download'
                }
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {
                'success': False,
                'message': 'Error interno del servidor',
                'errors': [str(e)]
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
