"""
batch_description_views.py - Vistas API para el módulo de planilla de descripción
"""

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import json
import logging
from datetime import datetime
from pathlib import Path
from io import BytesIO

from .batch_description_utils import INSFileParser, validate_ins_file

# Configurar logger
logger = logging.getLogger(__name__)


@api_view(['POST'])
@parser_classes((MultiPartParser, FormParser))
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
        file_bytes = uploaded_file.read()
        file_size_bytes = len(file_bytes)
        
        # Remove BOM if present
        if file_bytes.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
            file_bytes = file_bytes[3:]
        
        try:
            file_content = file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Intentar con otra codificación
            try:
                file_content = file_bytes.decode('latin-1')
            except:
                return Response(
                    {
                        'success': False,
                        'message': 'No se puede leer el archivo',
                        'errors': ['El archivo debe ser de texto UTF-8 o Latin-1']
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # DEBUG: Log file content con máximo detalle
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"=== DEBUG INS FILE ===")
        logger.error(f"File name: {uploaded_file.name}")
        logger.error(f"File size (bytes): {file_size_bytes}")
        logger.error(f"File content length (chars): {len(file_content)}")
        logger.error(f"First 100 chars: {repr(file_content[:100])}")
        logger.error(f"Last 150 chars: {repr(file_content[-150:])}")
        logger.error(f"Contains &&: {'&&' in file_content}")
        logger.error(f"Bytes value of last 50 chars: {file_bytes[-50:]}")
        logger.error(f"Character codes of last 30 chars: {[ord(c) for c in file_content[-30:]]}")
        
        # También en print para la consola
        print(f"=== DEBUG INS FILE ===")
        print(f"File name: {uploaded_file.name}")
        print(f"File size (bytes): {file_size_bytes}")
        print(f"File content length (chars): {len(file_content)}")
        print(f"First 100 chars: {repr(file_content[:100])}")
        print(f"Last 150 chars: {repr(file_content[-150:])}")
        print(f"Contains &&: {'&&' in file_content}")
        print(f"Character codes of last 30 chars: {[ord(c) for c in file_content[-30:]]}")
        
        # Validar estructura básica
        is_valid, error_msg = validate_ins_file(file_content)
        if not is_valid:
            logger.error(f"Validation failed: {error_msg}")
            print(f"Validation failed: {error_msg}")
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
        import traceback
        tb = traceback.format_exc()
        print(f"ERROR EN parse_ins_file: {str(e)}")
        print(tb)
        return Response(
            {
                'success': False,
                'message': 'Error interno del servidor',
                'errors': [str(e)],
                'debug': tb if settings.DEBUG else None
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_batch_description(request):
    """
    Endpoint para guardar datos de la planilla y generar PDF imprimible
    
    Expected POST data:
    {
        "header": {...},
        "pallets": [
            {
                "folio_pallet": "...",
                "cajas": int,
                "certificado_premuestreo": "...",
                "certificado_inspeccion": "...",
                "notas": "..."
            }
        ],
        "type": "NORMAL" | "ETAPA"
    }
    
    Returns:
        {
            "success": bool,
            "message": str,
            "pdf_url": str,
            "errors": []
        }
    """
    try:
        data = request.data
        
        # Validar datos requeridos
        if not data.get('header') or not data.get('pallets'):
            return Response(
                {
                    'success': False,
                    'message': 'Datos incompletos',
                    'errors': ['Se requieren header y pallets']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        header = data.get('header', {})
        pallets = data.get('pallets', [])
        batch_type = data.get('type', 'NORMAL')
        especie = data.get('especie') or header.get('especie', '')
        tipo_seleccion = data.get('tipo_seleccion', 'X')
        tipo_despacho = data.get('tipo_despacho', 'X')

        if not especie:
            return Response(
                {
                    'success': False,
                    'message': 'Falta la especie',
                    'errors': ['Debe ingresar la especie manualmente o proveerla en el archivo']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar PDF usando reportlab
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            logger.info("[SAVE_PDF] Iniciando generación de PDF")
            print("[SAVE_PDF] Iniciando generación de PDF")
            
            # Crear buffer para el PDF
            pdf_buffer = BytesIO()
            
            # Crear documento PDF - Tamaño legal para que quepa todo
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=0.3*inch,
                leftMargin=0.3*inch,
                topMargin=0.4*inch,
                bottomMargin=0.3*inch
            )
            
            # Elementos del documento
            elements = []
            styles = getSampleStyleSheet()
            
            # Header con Logo USDA a la derecha
            logo_text = ''
            if (Path(__file__).parent.parent / 'usda-logo.png').exists():
                try:
                    logo_path = Path(__file__).parent.parent / 'usda-logo.png'
                    logo = Image(str(logo_path), width=1.0*inch, height=1.0*inch)
                    
                    # Textos USDA
                    usda_text = '<b>U.S. Department of Agriculture</b><br/><font size="8">Animal and Plant Health Inspection Service</font>'
                    
                    # Header con titulo a la izquierda y logo+textos a la derecha
                    header_data = [
                        [
                            Paragraph('PLANILLA de DESCRIPCION del LOTE', ParagraphStyle(
                                'HeaderTitle',
                                parent=styles['Heading1'],
                                fontSize=14,
                                textColor=colors.HexColor('#000000'),
                                alignment=TA_LEFT,
                                fontName='Helvetica-Bold'
                            )),
                            logo
                        ],
                        [
                            '',
                            Paragraph(usda_text, ParagraphStyle(
                                'USDAText',
                                parent=styles['Normal'],
                                fontSize=8,
                                textColor=colors.HexColor('#000000'),
                                alignment=TA_CENTER,
                                fontName='Helvetica'
                            ))
                        ]
                    ]
                    
                    header_table = Table(header_data, colWidths=[4.0*inch, 1.5*inch])
                    header_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                        ('VALIGN', (1, 0), (1, 0), 'TOP'),
                        ('ALIGN', (1, 1), (1, 1), 'CENTER'),
                        ('VALIGN', (1, 1), (1, 1), 'TOP'),
                    ]))
                    elements.append(header_table)
                except Exception as e:
                    logger.warning(f"[SAVE_PDF] No se pudo cargar el logo: {e}")
                    title_style = ParagraphStyle(
                        'Title',
                        parent=styles['Heading1'],
                        fontSize=14,
                        textColor=colors.HexColor('#000000'),
                        spaceAfter=8,
                        alignment=TA_CENTER,
                        fontName='Helvetica-Bold'
                    )
                    title = Paragraph('PLANILLA de DESCRIPCION del LOTE', title_style)
                    elements.append(title)
            else:
                title_style = ParagraphStyle(
                    'Title',
                    parent=styles['Heading1'],
                    fontSize=14,
                    textColor=colors.HexColor('#000000'),
                    spaceAfter=8,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold'
                )
                title = Paragraph('PLANILLA de DESCRIPCION del LOTE', title_style)
                elements.append(title)
            
            elements.append(Spacer(1, 0.15*inch))
            
            # Info de la planilla - con campos editables
            info_data = [
                ['Lote Nº', header.get('sif', 'N/A'), '', 'Tipo Muestreo', batch_type],
                ['ESPECIE', especie, '', 'Tipo Selección', tipo_seleccion],
                ['', '', '', 'Tipo Despacho', tipo_despacho]
            ]
            
            info_table = Table(info_data, colWidths=[1.2*inch, 1.5*inch, 0.3*inch, 1.2*inch, 1.0*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('BACKGROUND', (3, 0), (3, -1), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (3, 0), (3, -1), colors.white),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('BACKGROUND', (4, 0), (4, -1), colors.white),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),
                ('TEXTCOLOR', (4, 0), (4, -1), colors.HexColor('#333333')),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTNAME', (4, 0), (4, -1), 'Helvetica'),
            ]))
            
            elements.append(info_table)
            elements.append(Spacer(1, 0.25*inch))
            
            # Tabla de pallets - Formato USDA
            pallet_data = [
                [
                    'FOLIO PALLET\nNº',
                    'Nº\nCajas',
                    'Nº CAJAS\nACUMULADO',
                    'Certificado de\npre muestreo',
                    'Nº\nCajas',
                    'Certificado de\ninspección',
                    'Nº\nCajas'
                ]
            ]
            
            # Calcular cajas acumuladas
            cajas_acumuladas = 0
            for idx, pallet in enumerate(pallets, 1):
                cajas_acumuladas += pallet.get('cajas', 0)
                pallet_data.append([
                    str(pallet.get('folio_pallet', '')),
                    str(pallet.get('cajas', '')),
                    str(cajas_acumuladas),
                    str(pallet.get('certificado_premuestreo', '')),
                    str(pallet.get('cajas', '')),
                    str(pallet.get('certificado_inspeccion', '')),
                    str(pallet.get('cajas', ''))
                ])
            
            pallet_table = Table(pallet_data, colWidths=[1.1*inch, 0.6*inch, 1.0*inch, 1.1*inch, 0.6*inch, 1.1*inch, 0.6*inch])
            pallet_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#333333')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(pallet_table)
            
            # Construir PDF
            logger.info("[SAVE_PDF] Construyendo PDF con reportlab")
            print("[SAVE_PDF] Construyendo PDF con reportlab")
            doc.build(elements)
            
            # Guardar PDF
            pdf_buffer.seek(0)
            filename = f"planilla_{header.get('sif', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            logger.info(f"[SAVE_PDF] Guardando archivo: {filename}")
            print(f"[SAVE_PDF] Guardando archivo: {filename}")
            
            # Guardar en media usando filesystem directo
            file_path = f"batch_descriptions/{filename}"
            
            # Crear subdirectorio si no existe
            media_root = Path(settings.MEDIA_ROOT)
            batch_dir = media_root / 'batch_descriptions'
            batch_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"[SAVE_PDF] Ruta del archivo: {batch_dir}")
            print(f"[SAVE_PDF] Ruta del archivo: {batch_dir}")
            
            # Guardar el archivo directamente en el sistema de archivos
            full_path = batch_dir / filename
            pdf_content = pdf_buffer.getvalue()
            pdf_size = len(pdf_content)
            
            logger.info(f"[SAVE_PDF] Tamaño del PDF en buffer: {pdf_size} bytes")
            print(f"[SAVE_PDF] Tamaño del PDF en buffer: {pdf_size} bytes")
            
            if pdf_size == 0:
                logger.error("[SAVE_PDF] ERROR: El PDF está vacío (tamaño = 0)")
                print("[SAVE_PDF] ERROR: El PDF está vacío (tamaño = 0)")
                return Response(
                    {
                        'success': False,
                        'message': 'Error al generar el PDF: archivo vacío',
                        'errors': ['El documento PDF generado está vacío']
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            with open(full_path, 'wb') as f:
                f.write(pdf_content)
            
            # Verificar que se guardó correctamente
            file_size = full_path.stat().st_size
            logger.info(f"[SAVE_PDF] Archivo guardado en: {full_path}")
            logger.info(f"[SAVE_PDF] Tamaño del archivo en disco: {file_size} bytes")
            print(f"[SAVE_PDF] Archivo guardado en: {full_path}")
            print(f"[SAVE_PDF] Tamaño del archivo en disco: {file_size} bytes")
            
            # Construir URL absoluta para el PDF
            relative_url = f"{settings.MEDIA_URL}{file_path}"
            pdf_url = request.build_absolute_uri(relative_url)
            
            logger.info(f"[SAVE_PDF] URL relativa: {relative_url}")
            print(f"[SAVE_PDF] URL relativa: {relative_url}")
            logger.info(f"[SAVE_PDF] URL absoluta generada: {pdf_url}")
            print(f"[SAVE_PDF] URL absoluta generada: {pdf_url}")
            print(f"[SAVE_PDF] MEDIA_URL: {settings.MEDIA_URL}")
            print(f"[SAVE_PDF] MEDIA_ROOT: {settings.MEDIA_ROOT}")
            
            return Response(
                {
                    'success': True,
                    'message': 'Planilla generada exitosamente',
                    'pdf_url': pdf_url,
                    'filename': filename
                },
                status=status.HTTP_200_OK
            )
            
        except ImportError as e:
            error_msg = f"ImportError en reportlab: {str(e)}"
            logger.error(f"[SAVE_PDF] {error_msg}")
            print(f"[SAVE_PDF] {error_msg}")
            
            return Response(
                {
                    'success': False,
                    'message': 'Librería de PDF no disponible',
                    'errors': ['Se requiere instalar reportlab: pip install reportlab', str(e)]
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"[SAVE_PDF] ERROR: {str(e)}")
        logger.error(f"[SAVE_PDF] Traceback: {tb}")
        print(f"ERROR EN save_batch_description: {str(e)}")
        print(tb)
        
        return Response(
            {
                'success': False,
                'message': 'Error al generar la planilla',
                'errors': [str(e)],
                'debug': tb if settings.DEBUG else None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
