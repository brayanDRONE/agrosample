"""
Parser for SAG dispatch planilla PDF files.
Extracts structured data from the official SAG planilla form.
"""
import re
import pdfplumber
from datetime import datetime
from typing import Dict, Optional


def parse_planilla_pdf(pdf_file_path: str) -> Dict:
    """
    Parse a SAG dispatch planilla PDF and extract all relevant fields.
    
    Args:
        pdf_file_path: Path to the PDF file
    
    Returns:
        dict: Extracted planilla data with keys mapped to the Multipuerto 42-field format
    
    Example output:
        {
            'folio_sag': '1385',
            'nro_planilla': '4',
            'agente': 'AG. DE AD. CARLO ROSSI SOFFIA',
            ...
        }
    """
    data = {}
    
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError('PDF has no pages')
            
            # Extract text from first page
            page = pdf.pages[0]
            text = page.extract_text()
            
            if not text:
                raise ValueError('Could not extract text from PDF')
            
            # Extract data using regex patterns
            data = _extract_fields(text)
            
    except Exception as e:
        raise ValueError(f'Error parsing PDF: {str(e)}')
    
    return data


def _extract_fields(text: str) -> Dict:
    """Extract fields from PDF text using regex patterns."""
    data = {}

    # --- ENCABEZADO ---
    data['folio_sag']       = _extract_value(text, r'Folio SAG\s*:\s*(\d+)')
    data['nro_planilla']    = _extract_value(text, r'Nro Planilla\s*:\s*N[°o]\s*(\d+)')
    data['agente']          = _extract_value(text, r'Agente\s*:\s*(.+?)(?=R\.U\.T|$)', multiline=True)
    data['rut_agente']      = _extract_value(text, r'R\.U\.T\.\s*:\s*([\d\-\w]+)')
    # Reg/Prov hasta "PLANILLA" o "Exportador"
    data['region_provincia']= _extract_value(text, r'Reg/Prov\s*:\s*([\d\w\s]+?)(?=PLANILLA|Exportador)', multiline=True)
    data['exportador']      = _extract_value(text, r'Exportador\s*:\s*(.+?)(?=R\.U\.T|$)', multiline=True)
    # segundo R.U.T. (el del exportador)
    rut_matches = re.findall(r'R\.U\.T\.\s*:\s*([\d\-\w]+)', text, re.IGNORECASE)
    data['rut_exportador']  = rut_matches[1] if len(rut_matches) > 1 else ''
    data['establecimiento'] = _extract_value(text, r'Facilitie\s*:\s*(.+?)(?=R\.U\.T|$)', multiline=True)
    data['nro_inscripcion'] = _extract_value(text, r'Nro\.\s*Incrip\.\s*:\s*(\d+)')
    data['nave']            = _extract_value(text, r'Nave\s*:\s*(.+?)(?=Puerto Destino|$)', multiline=True)
    data['puerto_destino']  = _extract_value(text, r'Puerto Destino:\s*(.+?)\s*/')
    data['pais_destino']    = _extract_value(text, r'Pais:\s*([A-Z\s]+?)(?=\n|Consignatario)')
    data['consignatario']   = _extract_value(text, r'Consignatario:\s*(.+?)(?=Identificaci[oó]n|$)', multiline=True)

    # --- IDENTIFICACIÓN DE CARGA ---
    data['fecha_despacho']      = _extract_date(text)
    data['oficina_sag_puerto']  = _extract_value(text, r'Oficina SAG Puerto:\s*(.+?)(?=Tipo Transporte|$)')
    data['tipo_transporte']     = _extract_value(text, r'Tipo Transporte:\s*([A-Z\s]+?)(?=Sellos|$)')
    data['sellos']              = _extract_value(text, r'Sellos:\s*(\d+)')
    data['guia_despacho']       = _extract_value(text, r'Guia Despacho:\s*(.*?)(?=Puerto Embarque)')
    data['puerto_embarque']     = _extract_value(text, r'Puerto Embarque:\s*([A-Z\s]+?)(?=Contenedor|$)')
    data['contenedor']          = _extract_value(text, r'Contenedor:\s*([A-Z0-9]+)')
    data['ubicacion']           = _extract_value(text, r'Ubicaci[oó]n:\s*(\d+)')
    data['patente']             = _extract_value(text, r'Patente:\s*([A-Z0-9/]+)')

    # --- TABLA DE ESPECIE (fila de datos) ---
    # La fila tiene la forma: "1 NARANJAS FUKUMOTO Fresco NARANJAS Convencional NO 1600 Cajas 15.00 24000.0 Kilogramos"
    data['especie']         = _extract_value(text, r'^\d+\s+([A-ZÁÉÍÓÚ]+)\s+\w+\s+(?:Fresco|Procesado)', multiline=True)
    data['variedad']        = _extract_value(text, r'^\d+\s+[A-ZÁÉÍÓÚ]+\s+([A-ZÁÉÍÓÚ]+)\s+(?:Fresco|Procesado)', multiline=True)
    data['condicion']       = _extract_value(text, r'^\d+\s+[A-ZÁÉÍÓÚ]+\s+\w+\s+(Fresco|Procesado)', multiline=True)
    data['producto']        = _extract_value(text, r'(?:Fresco|Procesado)\s+([A-ZÁÉÍÓÚ]+)\s+(?:Convencional|Org)', re.IGNORECASE)
    data['tipo_produccion'] = _extract_value(text, r'(?:Fresco|Procesado)\s+\w+\s+(Convencional|Org\w+)', re.IGNORECASE)
    data['transgenico']     = _extract_value(text, r'(?:Convencional|Org\w+)\s+(SI|NO)', re.IGNORECASE)
    data['cantidad_envases']= _extract_value(text, r'(?:SI|NO)\s+(\d+)\s+Cajas', re.IGNORECASE)
    data['tipo_envase']     = 'Cajas'  # siempre en planilla SAG
    # "Cajas 15.00 24000.0 Kilogramos"
    data['cantidad_unidad'] = _extract_value(text, r'Cajas\s+([\d.]+)\s+[\d.,]+\s+Kilogramos', re.IGNORECASE)
    data['cantidad_kg']     = _extract_value(text, r'Cajas\s+[\d.]+\s+([\d.,]+)\s+Kilogramos', re.IGNORECASE)

    # --- TOTALES ---
    data['total_pallets']   = _extract_value(text, r'Total de Pallets/bins:\s*(\d+)')
    # Total Cajas: 1.600 → quitar separador de miles (punto)
    raw_cajas = _extract_value(text, r'Total Cajas:\s*([\d.,]+)')
    data['total_cajas']     = raw_cajas.replace('.', '').replace(',', '')
    # Total Kilos: 24.000,0 → formato numérico chileno → convertir a decimal
    raw_kilos = _extract_value(text, r'Total Kilos:\s*([\d.,]+)')
    data['total_kilos']     = raw_kilos.replace('.', '').replace(',', '.')

    # --- ORIGEN Y DESPACHADOR ---
    # Línea: "Cachapoal PICHIDEGUA Folio Puerto:"
    data['provincia_origen']    = _extract_value(text, r'(\w+)\s+\w+\s+Folio Puerto')
    data['comuna_origen']       = _extract_value(text, r'\w+\s+(\w+)\s+Folio Puerto')
    # Línea: "Fecha Revisión: VICENTE CORTEZ"
    data['nombre_despachador']  = _extract_value(text, r'Fecha Revisi[oó]n:\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?)(?:\n|Aprobado|$)', multiline=True)

    # --- CONDICIÓN ---
    data['inspeccionado']   = bool(re.search(r'Inspeccionado:\s*X', text, re.IGNORECASE))
    data['tratado']         = bool(re.search(r'(?<!\w)Tratado\s+X', text, re.IGNORECASE))
    data['tratado_destino'] = bool(re.search(r'Tratado en Destino\s+X', text, re.IGNORECASE))

    # --- TRATAMIENTO CSG ---
    tratamiento_str = _extract_value(text, r'CSG\s+([\d\s]+)')
    data['tratamiento_csg'] = tratamiento_str.split() if tratamiento_str else []

    # Limpiar strings
    data = {k: (v.strip() if isinstance(v, str) else v) for k, v in data.items()}

    return data


def _extract_value(text: str, pattern: str, flags: int = re.IGNORECASE, multiline: bool = False) -> Optional[str]:
    """Extract a single value using regex."""
    if multiline:
        flags = flags | re.MULTILINE
    match = re.search(pattern, text, flags)
    if match:
        value = match.group(1) if match.lastindex else match.group(0)
        return value.strip()
    return ''


def _extract_date(text: str) -> str:
    """Extract and format the dispatch date."""
    date_match = re.search(r'Fecha Despacho:\s*(\d{2})/(\d{2})/(\d{4})', text)
    if date_match:
        day, month, year = date_match.groups()
        try:
            date_obj = datetime(int(year), int(month), int(day))
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return f'{year}-{month}-{day}'
    return ''


def map_planilla_to_multipuerto(planilla_data: Dict) -> Dict:
    """
    Map extracted planilla data to the 42-field Multipuerto format.
    
    Mapeo de 42 campos:
     1. codigo_exportadora
    2. folio_sag (Nro. Planilla es un correlativo interno de la planta)
     3. codigo_puerto_embarque
     4. codigo_puerto_destino
     5. tipo_transporte
     6. tipo_puerto_descarga
     7. patente_camion
     8. patente_carro (or guia_despacho → 00000 if empty)
     9. fecha_despacho
    10. nro_pallet_ubicacion
    11. cantidad_kg
    12. codigo_especie
    13. codigo_variedad
    14. codigo_establecimiento
    15. numero_contenedor
    16. codigo_tipo_envase
    17. codigo_csg
    18-23. muestreo_1 to 6
    24. cantidad_envases
    25. codigo_exportadora_alt
    26. total_kg_decimales
    27. ubicacion_sello
    28. campo_28 (empty)
    29. numero_sellos
    30-31. campos_30-31 (empty)
    32. tipo_produccion
    33. transgenico
    34. codigo_agencia_aduana
    35. campo_35 (empty)
    36. tratado
    37. campo_37 (empty)
    38. codigo_establecimiento_2
    39. reservado
    40. codigo_pais_destino
    41. codigo_pais_puerto_destino
    42. codigo_exportadora_final
    
    Args:
        planilla_data: dict from parse_planilla_pdf
    
    Returns:
        dict: Fields for build_dispatch_flat_file()
    """
    from .code_lookups import (
        lookup_puerto_codigo, lookup_especie_codigo, lookup_variedad_codigo,
        lookup_exportadora_codigo, lookup_pais_codigo, lookup_pais_puerto_codigo,
        get_codigo_transporte, get_codigo_tipo_envase,
        lookup_agencia_aduana_codigo, lookup_planta_codigo, lookup_producto_codigo,
        lookup_codigo_empresa_sag
    )
    
    # Parse patente (puede ser "PATENTE/REMOLQUE")
    patente = planilla_data.get('patente', '')
    patente_camion = ''
    patente_carro = ''
    if '/' in patente:
        patente_camion, patente_carro = patente.split('/', 1)
    else:
        patente_camion = patente
    
    # Parse tipo_produccion (1 = Convencional, 2 = Orgánico)
    tipo_prod = planilla_data.get('tipo_produccion', '').lower()
    codigo_tipo_produccion = '1' if 'convencional' in tipo_prod else '2' if 'org' in tipo_prod else ''
    
    # Parse transgenico (1 = SI, 0 = NO)
    transgenico_val = planilla_data.get('transgenico', '').upper()
    codigo_transgenico = '0' if 'NO' in transgenico_val else '1'
    
    # Parse cantidad_kg - asegurar 4 decimales exactos (campo 11)
    cantidad_kg_raw = planilla_data.get('cantidad_kg', '')
    if cantidad_kg_raw:
        try:
            cantidad_kg_val = float(str(cantidad_kg_raw).replace(',', '.'))
            cantidad_kg_formatted = f"{cantidad_kg_val:.4f}"
        except (ValueError, AttributeError):
            cantidad_kg_formatted = str(cantidad_kg_raw)
    else:
        cantidad_kg_formatted = ''
    
    # Campo 14 y 38: Código de establecimiento (registro de planta en SAG)
    # Buscar primero por nombre de establecimiento en el XML de SAG
    planta_nombre = planilla_data.get('establecimiento', '')
    codigo_planta = lookup_planta_codigo(planta_nombre)
    
    # Si no encuentra por nombre, usar nro_inscripcion solo como fallback
    if not codigo_planta:
        codigo_planta = planilla_data.get('nro_inscripcion', '')
    
    # Parse tratado
    codigo_tratado = '1' if planilla_data.get('tratado') else '0'
    
    # guia_despacho: si está vacío, se rellena con 00000 en OTRO campo, no en patente_carro
    guia_despacho = planilla_data.get('guia_despacho', '').strip()
    # Campo 8 siempre es patente_carro (NO se reemplaza con 00000)
    patente_carro_final = patente_carro if patente_carro else ''
    
    # Lookups
    puerto_embarque = planilla_data.get('puerto_embarque', '')
    codigo_puerto_embarque = lookup_puerto_codigo(puerto_embarque) or ''
    
    puerto_destino = planilla_data.get('puerto_destino', '')
    codigo_puerto_destino = lookup_puerto_codigo(puerto_destino) or ''
    
    especie = planilla_data.get('especie', '')
    variedad = planilla_data.get('variedad', '')
    codigo_especie = lookup_especie_codigo(especie, variedad) or ''
    codigo_variedad = lookup_variedad_codigo(variedad) or ''
    
    tipo_transporte = planilla_data.get('tipo_transporte', '')
    codigo_tipo_transporte = get_codigo_transporte(tipo_transporte) or ''
    
    tipo_envase = planilla_data.get('tipo_envase', '')
    codigo_tipo_envase_val = get_codigo_tipo_envase(tipo_envase) or '1'
    
    rut_exportador = planilla_data.get('rut_exportador', '')
    nombre_exportador = planilla_data.get('exportador', '')
    codigo_exportadora = lookup_exportadora_codigo(rut_exportador, nombre_exportador) or ''
    
    pais_destino = planilla_data.get('pais_destino', '')
    codigo_pais_destino = lookup_pais_codigo(pais_destino) or ''
    
    codigo_pais_puerto_destino = lookup_pais_puerto_codigo(puerto_destino) or ''
    
    # Campo 5: CODIGOPRODUCTO de EXPV_PRODUCTOS_ESPECIE_TC
    csg_codes = planilla_data.get('tratamiento_csg', [])
    tratado_bool = planilla_data.get('tratado', False)
    codigo_producto = lookup_producto_codigo(especie, variedad, csg_codes, bool(tratado_bool)) or ''
    
    payload = {
        'codigo_exportadora': codigo_planta,  # Campo 1: código SAG de la planta (175848)
        'nro_planilla': planilla_data.get('folio_sag', ''),
        'codigo_puerto_embarque': codigo_puerto_embarque,
        'codigo_puerto_destino': codigo_puerto_destino,
        'codigo_producto': codigo_producto,           # Campo 5: CODIGOPRODUCTO
        'tipo_transporte': codigo_tipo_transporte,    # Campo 6: tipo transporte
        'patente_camion': patente_camion,
        'patente_carro': patente_carro_final if patente_carro_final else '',
        'guia_despacho': guia_despacho,
        'fecha_despacho': planilla_data.get('fecha_despacho', ''),
        'nro_pallet_ubicacion': planilla_data.get('ubicacion', ''),
        'cantidad_kg': cantidad_kg_formatted,  # Campo 11: kg por pallet (formato #.0000)
        'codigo_especie': codigo_especie,
        'codigo_variedad': codigo_variedad,
        'codigo_establecimiento': codigo_planta,  # Campo 14: Nro. Inscripción del PDF
        'numero_contenedor': planilla_data.get('contenedor', ''),
        'codigo_tipo_envase': codigo_tipo_envase_val,
        'codigo_csg': '.'.join(planilla_data.get('tratamiento_csg', [])),  # Separador: punto, no coma
        'muestreo_1': '',
        'muestreo_2': '',
        'muestreo_3': '',
        'muestreo_4': '',
        'muestreo_5': '',
        'muestreo_6': '',
        'cantidad_envases': str(int(float(planilla_data.get('cantidad_unidad', '0') or '0'))),  # Campo 24: convertir a entero
        'codigo_exportadora_alt': '12',  # Campo 25: siempre 12 en formato Multipuerto
        'total_kg_decimales': planilla_data.get('total_kilos', '').replace('.', ',') if planilla_data.get('total_kilos') else '',
        'ubicacion_sello': '1',  # Default
        'numero_sellos': planilla_data.get('sellos', ''),
        'tipo_produccion': codigo_tipo_produccion,
        'transgenico': codigo_transgenico,
        'codigo_agencia_aduana': lookup_agencia_aduana_codigo(planilla_data.get('agente', '')) or planilla_data.get('agente', '')[:6],
        'tratado': codigo_tratado,
        'codigo_establecimiento_2': codigo_planta,  # Campo 38: Nro. Inscripción (igual al campo 14)
        'reservado': 'DELEGADO',
        'codigo_pais_destino': codigo_pais_destino,
        'codigo_pais_puerto_destino': lookup_pais_puerto_codigo(puerto_destino) or '',
        'codigo_exportadora_final': codigo_planta,  # Campo 42: código de planta (debe coincidir con campo 14)
    }
    
    return payload
