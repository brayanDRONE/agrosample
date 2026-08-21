"""Lectura y normalizacion de archivos Excel para validacion de SDP."""

import re
import unicodedata

from openpyxl import load_workbook


FIELD_ALIASES = {
    'csg': ('csg', 'codigo csg', 'codigo sag', 'codigosag', 'codigo'),
    'provincia': ('provincia origen', 'provincia', 'provincia pack'),
    'comuna': ('comuna origen', 'comuna', 'comuna pack'),
    'variedad_real': {
        'variedad real', 'variedadreal', 'variedad agronomica', 'variedad agron mica'
    },
    'variedad_rotulada': {
        'variedad rotulada', 'variedadrotulada', 'variedad comercial'
    },
    'sdp': {'sdp', 'sdp sector', 'sitio de produccion', 'sitio produccion'},
}


def normalize_header(value):
    """Normaliza un encabezado para compararlo sin acentos ni formato."""
    text = '' if value is None else str(value)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def normalize_value(value):
    """Convierte valores Excel a texto estable sin perder codigos SAG."""
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def extract_workbook_metadata(worksheet):
    """Extrae el numero de lote desde el bloque superior de la hoja."""
    metadata = {'numero_lote': ''}
    top_rows = list(worksheet.iter_rows(min_row=1, max_row=6, values_only=True))

    for row in top_rows:
        for index, value in enumerate(row):
            label = normalize_header(value)
            if 'inspeccion sag' not in label:
                continue
            for candidate in row[index + 1:]:
                normalized = normalize_value(candidate)
                if normalized:
                    metadata['numero_lote'] = normalized
                    return metadata

    return metadata


def resolve_columns(headers):
    normalized = {normalize_header(header): index for index, header in enumerate(headers)}
    columns = {}
    missing = []

    for field, aliases in FIELD_ALIASES.items():
        match = next((normalized[alias] for alias in aliases if alias in normalized), None)
        if match is None:
            missing.append(field)
            continue
        columns[field] = match

    return columns, missing


def parse_sdp_workbook(file_object):
    """Lee todas las hojas y devuelve filas normalizadas y SDP unicos."""
    workbook = load_workbook(file_object, read_only=True, data_only=True)
    rows = []
    sheets = []
    errors = []
    metadata = {'numero_lote': ''}

    try:
        for worksheet in workbook.worksheets:
            sheets.append(worksheet.title)
            if not metadata['numero_lote']:
                metadata = extract_workbook_metadata(worksheet)
            values = worksheet.iter_rows(values_only=True)
            header_row_number = None
            headers = None
            buffered_rows = []
            for row_number, candidate in enumerate(values, start=1):
                buffered_rows.append((row_number, candidate))
                columns, missing = resolve_columns(candidate)
                if len(missing) <= 1 and len(columns) >= 5:
                    headers = candidate
                    header_row_number = row_number
                    break
                if row_number >= 30:
                    break

            if headers is None:
                continue

            columns, missing = resolve_columns(headers)
            if missing:
                errors.append(
                    f"Hoja '{worksheet.title}': faltan columnas requeridas: {', '.join(missing)}"
                )
                continue

            for row_number, values_row in enumerate(values, start=header_row_number + 1):
                record = {
                    field: normalize_value(values_row[index] if index < len(values_row) else None)
                    for field, index in columns.items()
                }
                if not any(record.values()):
                    continue
                record['hoja'] = worksheet.title
                record['fila_excel'] = row_number
                rows.append(record)
    finally:
        workbook.close()

    unique_sdps = list(dict.fromkeys(row['sdp'] for row in rows if row['sdp']))
    return {
        'sheets': sheets,
        'metadata': metadata,
        'rows': rows,
        'unique_sdps': unique_sdps,
        'errors': errors,
    }