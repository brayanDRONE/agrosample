"""Vista del flujo Excel -> consulta SAG -> consolidado -> PDF."""

import logging
import re
import unicodedata
from datetime import datetime
from io import BytesIO
from pathlib import Path

from django.conf import settings
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .sag_sdp_service import SagSdpService
from .sdp_excel_parser import parse_sdp_workbook


logger = logging.getLogger(__name__)


def _normalize_text(value):
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return ' '.join(text.upper().split())


def _normalize_compact(value):
    return re.sub(r'[^A-Z0-9]', '', _normalize_text(value))


def _merge_excel_rows(rows):
    """Consolida los registros del Excel dejando una fila por SDP."""
    grouped = {}
    for row in rows:
        grouped.setdefault(row['sdp'], []).append(row)

    consolidated = []
    for sdp, sdp_rows in grouped.items():
        def unique_values(field):
            return list(dict.fromkeys(row[field] for row in sdp_rows if row[field]))

        consolidated.append({
            'csg': ', '.join(unique_values('csg')),
            'provincia': ', '.join(unique_values('provincia')),
            'comuna': ', '.join(unique_values('comuna')),
            'variedad_comercial': ', '.join(unique_values('variedad_rotulada')),
            'sdp': sdp,
            'registros_excel': len(sdp_rows),
        })
    return consolidated


def _compare_row(row, sag_result):
    data = sag_result.get('datos')
    if sag_result['status'] != 'FOUND' or not data:
        return {
            **row,
            'sag_status': sag_result['status'],
            'datos_sag': None,
            'cumple': False,
            'diferencias': ['SDP no encontrado en SAG'] if sag_result['status'] == 'NOT_FOUND' else [
                f"Consulta SAG: {sag_result['status']}"
            ],
        }

    differences = []
    comuna_match = _normalize_text(row['comuna']) == _normalize_text(data['comuna'])
    if not comuna_match:
        differences.append(f"Comuna Excel '{row['comuna']}' vs SAG '{data['comuna']}'")

    sag_variety = _normalize_compact(data['variedad'])
    commercial_variety = _normalize_compact(row['variedad_comercial'])
    variety_match = bool(commercial_variety) and (
        commercial_variety == sag_variety or commercial_variety in sag_variety
    )
    if not variety_match:
        differences.append(
            f"Variedad comercial Excel '{row['variedad_comercial']}' vs SAG '{data['variedad']}'"
        )

    if not data['muestreo_lote']:
        differences.append('SAG no autoriza muestreo de lote')

    return {
        **row,
        'sag_status': 'FOUND',
        'datos_sag': {key: value for key, value in data.items() if key not in {'raw_row', 'raw_match'}},
        'comparacion': {
            'comuna': comuna_match,
            'variedad_comercial': variety_match,
            'muestreo_lote': data['muestreo_lote'],
        },
        'cumple': data['muestreo_lote'] and comuna_match and variety_match,
        'diferencias': differences,
    }


def _build_summary_pdf(results, filename, numero_lote):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.25 * inch,
        leftMargin=0.25 * inch,
        topMargin=0.3 * inch,
        bottomMargin=0.3 * inch,
    )
    styles = getSampleStyleSheet()
    body_style = styles['BodyText'].clone('SdpBody')
    body_style.fontSize = 7
    body_style.leading = 8
    title_style = styles['Title'].clone('SdpTitle')
    title_style.fontSize = 15

    generated_date = datetime.now().strftime('%d/%m/%Y')
    elements = [Paragraph('REPORTE RESUMIDO DE VALIDACION SDP', title_style)]
    elements.append(Paragraph(
        f"Numero de lote: {numero_lote or 'No informado'} | Fecha de generacion: {generated_date}",
        body_style,
    ))
    elements.append(Spacer(1, 0.12 * inch))
    headers = ['CSG', 'SDP', 'Provincia Excel', 'Comuna Excel', 'Variedad Comercial', 'Productor', 'Estado', 'Observaciones']
    table_data = [headers]
    for result in results:
        sag = result.get('datos_sag') or {}
        table_data.append([
            result['csg'], result['sdp'], result['provincia'], result['comuna'], result['variedad_comercial'],
            sag.get('productor', ''), 'CUMPLE' if result['cumple'] else 'NO CUMPLE',
            '; '.join(result['diferencias']) or 'Sin diferencias',
        ])

    widths = [0.9, 0.7, 1.0, 1.05, 1.35, 1.8, 0.8, 3.25]
    wrapped_data = [[Paragraph(str(cell), body_style) for cell in row] for row in table_data]
    table = Table(wrapped_data, colWidths=[width * inch for width in widths], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#14532d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('LEADING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#94a3b8')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
        ('TEXTCOLOR', (6, 1), (6, -1), colors.HexColor('#166534')),
    ]))
    elements.append(table)
    document.build(elements)
    buffer.seek(0)
    media_dir = Path(settings.MEDIA_ROOT) / 'sdp_validation'
    media_dir.mkdir(parents=True, exist_ok=True)
    path = media_dir / filename
    path.write_bytes(buffer.getvalue())
    return path, len(buffer.getvalue())


@api_view(['POST'])
@parser_classes((MultiPartParser, FormParser))
@permission_classes([IsAuthenticated])
def validate_sdp_excel(request):
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({'success': False, 'message': 'Debe seleccionar un archivo Excel'}, status=status.HTTP_400_BAD_REQUEST)
    if not uploaded_file.name.lower().endswith(('.xlsx', '.xlsm')):
        return Response({'success': False, 'message': 'El archivo debe ser .xlsx o .xlsm'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        parsed = parse_sdp_workbook(uploaded_file)
        if parsed['errors']:
            return Response({'success': False, 'message': 'El Excel no tiene las columnas requeridas', 'errors': parsed['errors']}, status=status.HTTP_400_BAD_REQUEST)

        service = SagSdpService()
        sag_cache = {sdp: service.query(sdp) for sdp in parsed['unique_sdps']}
        consolidated_rows = _merge_excel_rows(parsed['rows'])
        results = [_compare_row(row, sag_cache[row['sdp']]) for row in consolidated_rows]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'validacion_sdp_{timestamp}.pdf'
        pdf_path, pdf_size = _build_summary_pdf(
            results,
            filename,
            parsed['metadata'].get('numero_lote', ''),
        )
        counts = {
            'total': len(results),
            'cumplen': sum(1 for result in results if result['cumple']),
            'no_cumplen': sum(1 for result in results if not result['cumple']),
            'consultas_unicas': len(parsed['unique_sdps']),
        }
        return Response({
            'success': True,
            'message': 'Validacion completada',
            'sheets': parsed['sheets'],
            'numero_lote': parsed['metadata'].get('numero_lote', ''),
            'fecha_generacion': datetime.now().strftime('%d/%m/%Y'),
            'summary': counts,
            'results': results,
            'pdf_url': request.build_absolute_uri(f'{settings.MEDIA_URL}sdp_validation/{filename}'),
            'pdf_size': pdf_size,
        })
    except Exception as error:
        logger.exception('[SDP] Error procesando Excel')
        return Response({'success': False, 'message': 'No se pudo procesar el Excel', 'errors': [str(error)]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)