"""
Code lookup functions for mapping SAG planilla data to Multipuerto codes.
Hardcoded lookups + XML/CSV file support.
"""
import os
import xml.etree.ElementTree as ET
from typing import Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

# Cache for loaded data
_PLANTAS_CACHE = None
_EXPORTADORAS_CACHE = None


# ============================================================================
# HARDCODED LOOKUPS - Datos conocidos del sistema Multipuerto
# ============================================================================

PUERTOS_MAP = {
    'VALPARAISO': '56',
    'PUERTO QUETZAL': '107',
    'PUERTO MONTT': '12',
    'ANTOFAGASTA': '45',
    'IQUIQUE': '30',
}

PAISES_MAP = {
    'GUATEMALA': '23',
    'MEXICO': '24',
    'USA': '15',
    'CANADA': '11',
    'CHILE': '17',
    'CHINA': '21',
    'JAPON': '22',
    'COREA': '28',
    'ESPAÑA': '34',
    'RUSIA': '36',
}

PAIS_PUERTO_MAP = {
    'PUERTO QUETZAL': '120877',
    'VALPARAISO': '90001',
    'ANTOFAGASTA': '90002',
    'PUERTO MONTT': '90003',
}

TIPO_TRANSPORTE_MAP = {
    'CONTENEDOR': '5',
    'CAMION': '1',
    'CAMION FRIGORICO': '2',
    'AEREO': '3',
    'MARITIMO': '4',
}

# Mapa de código de producto (CODIGOPRODUCTO) de EXPV_PRODUCTOS_ESPECIE_TC
# Clave: (ESPECIE_UPPER, TIPO_TRATAMIENTO)  tipo: 'FRESCO', 'CON_TRATAMIENTO', 'BROMURO', 'FOSFURO', 'FRIO'
PRODUCTOS_MAP = {
    ('NARANJA', 'FRESCO'): '15',
    ('NARANJAS', 'FRESCO'): '15',
    ('NARANJA', 'CON_TRATAMIENTO'): '2624',
    ('NARANJAS', 'CON_TRATAMIENTO'): '2624',
    ('NARANJA', 'BROMURO'): '6601',
    ('NARANJAS', 'BROMURO'): '6601',
    ('NARANJA', 'FOSFURO'): '6602',
    ('NARANJAS', 'FOSFURO'): '6602',
    ('NARANJA', 'FRIO'): '3289',
    ('NARANJAS', 'FRIO'): '3289',
    ('UVA', 'FRESCO'): '5',
    ('UVAS', 'FRESCO'): '5',
    ('MANZANA', 'FRESCO'): '1',
    ('MANZANAS', 'FRESCO'): '1',
    ('PERA', 'FRESCO'): '16',
    ('PERAS', 'FRESCO'): '16',
    ('KIWI', 'FRESCO'): '18',
    ('LIMON', 'FRESCO'): '20',
    ('LIMONES', 'FRESCO'): '20',
}

TIPO_ENVASE_MAP = {
    'CAJAS': '4',
    'BINS': '27',
    'PALLETS': '3',
    'BOLSAS': '4',
}

# Especies y variedades comunes
ESPECIES_MAP = {
    ('NARANJAS', 'FUKUMOTO'): '4',
    ('UVAS', 'SUPERIOR'): '1',
    ('MANZANAS', 'GALA'): '2',
    ('PERAS', 'CONFERENCE'): '3',
}

EXPORTADORAS_MAP = {
    # Hardcoded mappings should only contain VERIFIED values
    # Most data will load from XML dynamically
}

AGENCIAS_MAP = {
    'CARLO ROSSI': 'PTXT92',
    'AG. DE AD. CARLO ROSSI': 'PTXT92',
    'CARLO ROSSI SOFFIA': 'PTXT92',
}

# Plantas (Establecimientos) - Mapeo de nombre → código de registro
PLANTAS_MAP = {
    'INMOBILIARIA E INVERSIONES LOS ROBLES S.A.': '175848',
    'INMOBILIARIA E INVERSIONES LOS ROBLES': '175848',
    'LOS ROBLES': '175848',
}

# Mapeo de plantas a código de empresa en SAG (para campo 1 del archivo plano)
# Campo 1 debe ser el código de la PLANTA (no exportadora)
# La planta es la empresa principal que posee y controla el despacho
PLANTAS_CODIGO_EMPRESA_SAG = {
    '175848': '175848',  # INMOBILIARIA E INVERSIONES LOS ROBLES S.A. - la empresa principal
}


# ============================================================================
# FUNCIONES DE LOOKUP
# ============================================================================

def lookup_puerto_codigo(puerto_nombre: str) -> Optional[str]:
    """Lookup port code by port name."""
    if not puerto_nombre:
        return None
    
    puerto_upper = puerto_nombre.upper().strip()
    return PUERTOS_MAP.get(puerto_upper)


def lookup_pais_codigo(pais_nombre: str) -> Optional[str]:
    """Lookup country code by country name."""
    if not pais_nombre:
        return None
    
    pais_upper = pais_nombre.upper().strip()
    return PAISES_MAP.get(pais_upper)


def lookup_pais_puerto_codigo(puerto_nombre: str) -> Optional[str]:
    """Lookup country-port code (PAIS_PUERTO) by port name."""
    if not puerto_nombre:
        return None
    
    puerto_upper = puerto_nombre.upper().strip()
    return PAIS_PUERTO_MAP.get(puerto_upper)


def lookup_especie_codigo(especie_nombre: str, variedad_nombre: str = '') -> Optional[str]:
    """Lookup species code by species and variety name."""
    if not especie_nombre:
        return None
    
    especie_upper = especie_nombre.upper().strip()
    variedad_upper = (variedad_nombre.upper().strip() if variedad_nombre else '')
    
    # Try exact match with variety
    if variedad_upper:
        key = (especie_upper, variedad_upper)
        if key in ESPECIES_MAP:
            return ESPECIES_MAP[key]
    
    # Try species-only match
    for (esp, var), codigo in ESPECIES_MAP.items():
        if esp == especie_upper:
            return codigo
    
    return None


def lookup_variedad_codigo(variedad_nombre: str) -> Optional[str]:
    """Lookup variety code by variety name (returns same as especie for now)."""
    if not variedad_nombre:
        return None
    
    variedad_upper = variedad_nombre.upper().strip()
    
    # For now, varieties usually have same code as species
    for (esp, var), codigo in ESPECIES_MAP.items():
        if var == variedad_upper:
            return codigo
    
    return None


def lookup_exportadora_codigo(rut_exportador: str = '', nombre_exportador: str = '') -> Optional[str]:
    """
    Lookup exporter code by RUT or exporter name.
    Loads dynamically from EXPORTADORA XML if not in hardcoded map.
    
    Example: 
      - by RUT: '77076859-4' (if available in XML)
      - by name: 'PROVIDENCE EXPORTS S.A.' → '6604'
    """
    if not rut_exportador and not nombre_exportador:
        return None
    
    # Try hardcoded map first if RUT provided
    if rut_exportador:
        rut_clean = rut_exportador.strip()
        if rut_clean in EXPORTADORAS_MAP:
            return EXPORTADORAS_MAP[rut_clean]
    
    # Try by name if provided
    if nombre_exportador:
        nombre_upper = nombre_exportador.upper().strip()
        
        # Try hardcoded map by name
        for key, codigo in EXPORTADORAS_MAP.items():
            if key.upper() == nombre_upper or nombre_upper in key.upper():
                return codigo
    
    # Load from XML if not in hardcoded map
    try:
        global _EXPORTADORAS_CACHE
        if _EXPORTADORAS_CACHE is None:
            _EXPORTADORAS_CACHE = _load_exportadoras_from_xml()
        
        # Try by RUT if available
        if rut_exportador:
            rut_clean = rut_exportador.strip()
            if rut_clean in _EXPORTADORAS_CACHE:
                return _EXPORTADORAS_CACHE[rut_clean]
        
        # Try by name
        if nombre_exportador:
            nombre_upper = nombre_exportador.upper().strip()
            if nombre_upper in _EXPORTADORAS_CACHE:
                return _EXPORTADORAS_CACHE[nombre_upper]
            
            # Try partial name match
            for key, codigo in _EXPORTADORAS_CACHE.items():
                if isinstance(key, str) and (key in nombre_upper or nombre_upper in key):
                    return codigo
    
    except Exception as e:
        pass  # If XML loading fails, continue with None
    
    return None


def _load_exportadoras_from_xml() -> Dict[str, str]:
    """
    Load exporter codes from EXPORTADORA XML file.
    Maps both by RUT (if available) and by name.
    """
    exportadoras = {}
    
    try:
        exportadora_xml = os.path.join(DATA_DIR, 'EXPORTADORA (1).xml')
        if not os.path.exists(exportadora_xml):
            return exportadoras
        
        tree = ET.parse(exportadora_xml)
        root = tree.getroot()
        
        # Buscar todos los registros de exportador
        for row in root.findall('.//{*}row'):
            codigo = None
            nombre = None
            rut = None
            
            for child in row:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                if tag == 'CODIGOEXPORTADORA':
                    codigo = child.text
                elif tag == 'NOMBREEXPORTADORA':
                    nombre = child.text
                elif tag == 'RUTNACIONAL':
                    rut = child.text
                elif tag == 'RUTN':  # Alternative RUT field name
                    rut = child.text
            
            if codigo:
                # Map by RUT if available
                if rut:
                    exportadoras[rut.strip()] = codigo
                
                # Map by name (primary key for lookups)
                if nombre:
                    exportadoras[nombre.upper().strip()] = codigo
    
    except Exception as e:
        print(f"Warning: Could not load EXPORTADORA XML: {e}")
    
    return exportadoras


def lookup_agencia_aduana_codigo(agencia_nombre: str) -> Optional[str]:
    """Lookup customs agency code by agency name."""
    if not agencia_nombre:
        return None
    
    agencia_upper = agencia_nombre.upper().strip()
    
    # Try exact match
    for nombre, codigo in AGENCIAS_MAP.items():
        if nombre.upper() == agencia_upper:
            return codigo
    
    # Try partial match
    for nombre, codigo in AGENCIAS_MAP.items():
        if nombre.upper() in agencia_upper or agencia_upper in nombre.upper():
            return codigo
    
    return None


def get_codigo_transporte(tipo_transporte: str) -> str:
    """Get transport type code."""
    if not tipo_transporte:
        return ''
    
    tipo_upper = tipo_transporte.upper().strip()
    return TIPO_TRANSPORTE_MAP.get(tipo_upper, '')


def get_codigo_tipo_envase(tipo_envase: str) -> str:
    """Get container type code."""
    if not tipo_envase:
        return '1'  # Default to boxes
    
    tipo_upper = tipo_envase.upper().strip()
    return TIPO_ENVASE_MAP.get(tipo_upper, '1')


def lookup_codigo_empresa_sag(codigo_planta: str) -> Optional[str]:
    """
    Lookup SAG company code (for field 1) by plant registration code.
    
    Args:
        codigo_planta: Plant registration code (NUMERODEREGISTRODEPLANTA)
    
    Returns:
        SAG company code for field 1, or None
    """
    if not codigo_planta:
        return None
    
    return PLANTAS_CODIGO_EMPRESA_SAG.get(codigo_planta)


def lookup_planta_codigo(planta_nombre: str) -> Optional[str]:
    """
    Lookup plant registration code by plant name.
    
    Tries multiple strategies:
    1. Hardcoded PLANTAS_MAP
    2. Fuzzy search in PLANTAS_MAP
    3. Load from PLANTA XML file
    4. Fuzzy search in XML
    
    Example: 'Inmobiliaria e Inversiones Los Robles S.A.' → '175848'
    """
    if not planta_nombre:
        return None
    
    planta_upper = planta_nombre.upper().strip()
    
    # Strategy 1: Try exact match in hardcoded map
    for nombre, codigo in PLANTAS_MAP.items():
        if nombre.upper() == planta_upper:
            return codigo
    
    # Strategy 2: Try partial match in hardcoded map
    for nombre, codigo in PLANTAS_MAP.items():
        if nombre.upper() in planta_upper or planta_upper in nombre.upper():
            return codigo
    
    # Strategy 3: Load from XML and search by name
    try:
        global _PLANTAS_CACHE
        if _PLANTAS_CACHE is None:
            _PLANTAS_CACHE = _load_plantas_from_xml()
        
        # Try exact match in XML
        if planta_upper in _PLANTAS_CACHE:
            return _PLANTAS_CACHE[planta_upper]
        
        # Try partial match in XML
        for nombre_xml, codigo in _PLANTAS_CACHE.items():
            if nombre_xml in planta_upper or planta_upper in nombre_xml:
                return codigo
    except Exception as e:
        pass  # If XML loading fails, continue with None
    
    return None


def lookup_producto_codigo(especie: str, variedad: str = '', csg_codes=None, tratado: bool = False) -> Optional[str]:
    """
    Lookup product code (CODIGOPRODUCTO) from EXPV_PRODUCTOS_ESPECIE_TC.
    
    Args:
        especie: Species name (e.g., 'NARANJAS')
        variedad: Variety name (e.g., 'FUKUMOTO') - not used yet, reserved for future
        csg_codes: List of CSG treatment codes (presence indicates treatment)
        tratado: Boolean indicating if the product has been treated
    
    Returns:
        CODIGOPRODUCTO string, or None if not found
    
    Examples:
        lookup_producto_codigo('NARANJAS', 'FUKUMOTO', ['123106'], False) → '2624'
        lookup_producto_codigo('NARANJAS', 'FUKUMOTO', [], False) → '15'
    """
    if not especie:
        return None
    
    especie_upper = especie.upper().strip()
    
    # Determine treatment type
    has_treatment = bool(csg_codes) or bool(tratado)
    tipo = 'CON_TRATAMIENTO' if has_treatment else 'FRESCO'
    
    # Try exact match with treatment type
    key = (especie_upper, tipo)
    if key in PRODUCTOS_MAP:
        return PRODUCTOS_MAP[key]
    
    # Try FRESCO as fallback
    key_fresco = (especie_upper, 'FRESCO')
    if key_fresco in PRODUCTOS_MAP:
        return PRODUCTOS_MAP[key_fresco]
    
    # Try partial match by species name
    for (esp, _tipo), codigo in PRODUCTOS_MAP.items():
        if esp in especie_upper or especie_upper in esp:
            return codigo
    
    return None


def _load_plantas_from_xml() -> Dict[str, str]:
    """Load plant names and codes from PLANTA XML file."""
    plantas = {}
    
    try:
        planta_xml = os.path.join(DATA_DIR, 'PLANTA (1) (1).xml')
        if not os.path.exists(planta_xml):
            return plantas
        
        tree = ET.parse(planta_xml)
        root = tree.getroot()
        
        # Buscar todos los registros de planta
        for row in root.findall('.//{*}row'):
            registro = None
            nombre = None
            
            for child in row:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                if tag == 'NUMERODEREGISTRODEPLANTA':
                    registro = child.text
                elif tag == 'NOMBREPLANTA':
                    nombre = child.text
            
            if registro and nombre:
                # Add both the exact name and variants to the cache
                plantas[nombre.upper().strip()] = registro
                # Also add without extra whitespace
                plantas[' '.join(nombre.upper().strip().split())] = registro
    
    except Exception as e:
        print(f"Warning: Could not load PLANTA XML: {e}")
    
    return plantas
