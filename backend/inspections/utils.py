"""
Utilidades para cálculo de muestreo.
"""
import math
import random


# ==================== CLASIFICACIÓN DE ESPECIES ====================

ESPECIES_HIPERGEOMETRICA_3 = [
    'Damasco',
    'Damascos',
    'Damasco 3%',
]

ESPECIES_HIPERGEOMETRICA_6 = [
    'Ciruela',
    'Ciruelas',
    'Damasco_condicional',
    'Damasco 6%',
    'Durazno',
    'Duraznos',
    'Nectarino',
    'Nectarinos',
    'Nectarin',
    'Nectarines',
    'Plumcot',
    'Plumcots',
    'Uchuva',
    'Uchuvas',
    'Cranberry',
    'Cranberries',
]

ESPECIES_BIOMETRICA = [
    'Manzana',
    'Manzanas',
    'Pera',
    'Peras',
    'Pera Asiática',
    'Peras Asiáticas',
    'Clementina',
    'Clementinas',
    'Tangerina',
    'Tangerinas',
    'Mandarina',
    'Mandarinas',
    'Naranja',
    'Naranjas',
    'Granada',
    'Granadas',
    'Baby Kiwi',
    'Baby Kiwis',
    'Kiwi',
    'Kiwis',
    'Pomelo',
    'Pomelos',
    'Limón',
    'Limones',
    'Chirimoya_condicional',
    'Chirimoyas_condicional',
]

# ==================== TABLAS DE MUESTREO OFICIALES SAG-USDA ====================

# Tabla Hipergeométrica 3% (3% infestación - 95% confianza)
# Especie: Damasco (sin frío autorizado)
TABLA_HIPERGEOMETRICA_3 = [
    (1, 900, None),      # Todas las unidades
    (901, 1500, 63),
    (1501, 4000, 90),
    (4001, 10000, 94),
    (10001, 15000, 96),
    (15001, 20000, 98),
    (20001, float('inf'), 99),
]

# Tabla Hipergeométrica 6% (6% infestación - 95% confianza)
# Especies: Ciruela, Durazno, Nectarino, Plumcot, Uchuva, Cranberry, Damasco (con frío)
# 🚨 LÍMITE MÁXIMO: 49 unidades
TABLA_HIPERGEOMETRICA_6 = [
    (1, 37, None),       # Todas las unidades
    (38, 78, 37),
    (79, 88, 38),
    (89, 117, 39),
    (118, 140, 40),
    (141, 157, 41),
    (158, 175, 42),
    (176, 207, 43),
    (208, 257, 44),
    (258, 335, 45),
    (336, 425, 46),
    (426, 850, 47),
    (851, 2250, 48),
    (2251, float('inf'), 49),  # LÍMITE MÁXIMO ABSOLUTO: 49
]

# Tabla Biométrica
# Especies: Manzana, Pera, Pera Asiática, Clementina, Tangerina, Mandarina, 
#           Naranja, Granada, Baby Kiwi, Kiwi, Pomelo, Limón, Chirimoya (Systems Approach)
TABLA_BIOMETRICA = [
    (1, 30, None),       # Todas las unidades
    (31, 2000, 30),
    (2001, 10000, 50),
    (10001, float('inf'), 100),
]


def obtener_tipo_tabla_muestreo(especie):
    """
    Determina qué tipo de tabla de muestreo usar según la especie.
    
    Args:
        especie (str): Nombre de la especie
    
    Returns:
        str: Tipo de tabla ('HIPERGEOMETRICA_3', 'HIPERGEOMETRICA_6', 'BIOMETRICA', 'PORCENTUAL')
    """
    # Normalizar la especie para comparación case-insensitive
    especie_lower = especie.lower() if especie else ''
    
    # Crear versiones normalizadas de las listas
    especies_h3_lower = [e.lower() for e in ESPECIES_HIPERGEOMETRICA_3]
    especies_h6_lower = [e.lower() for e in ESPECIES_HIPERGEOMETRICA_6]
    especies_bio_lower = [e.lower() for e in ESPECIES_BIOMETRICA]
    
    if especie_lower in especies_h3_lower:
        return 'HIPERGEOMETRICA_3'
    elif especie_lower in especies_h6_lower:
        return 'HIPERGEOMETRICA_6'
    elif especie_lower in especies_bio_lower:
        return 'BIOMETRICA'
    else:
        return 'PORCENTUAL'


def permite_incremento_intensidad(especie):
    """
    Determina si una especie permite incremento de intensidad de muestreo.
    
    Solo las especies con tabla BIOMÉTRICA o PORCENTUAL permiten incremento.
    Las especies con tabla HIPERGEOMÉTRICA NO permiten incremento.
    
    Args:
        especie (str): Nombre de la especie
    
    Returns:
        bool: True si permite incremento, False si no
    """
    tipo_tabla = obtener_tipo_tabla_muestreo(especie)
    return tipo_tabla in ['BIOMETRICA', 'PORCENTUAL']


def calcular_tamano_muestra_por_tabla(tamano_lote, tipo_tabla):
    """
    Calcula el tamaño de muestra según la tabla de muestreo SAG-USDA oficial.
    
    Args:
        tamano_lote (int): Tamaño total del lote
        tipo_tabla (str): Tipo de tabla a usar
    
    Returns:
        tuple: (tamano_muestra: int, nombre_tabla: str)
    """
    if tipo_tabla == 'HIPERGEOMETRICA_3':
        tabla = TABLA_HIPERGEOMETRICA_3
        nombre = 'Hipergeométrica del 3%'
    elif tipo_tabla == 'HIPERGEOMETRICA_6':
        tabla = TABLA_HIPERGEOMETRICA_6
        nombre = 'Hipergeométrica del 6%'
    elif tipo_tabla == 'BIOMETRICA':
        tabla = TABLA_BIOMETRICA
        nombre = 'Biométrica'
    else:  # PORCENTUAL
        # Reglas especiales para Porcentual 2%
        if tamano_lote <= 100:
            tamano_muestra = 2
        else:
            # Calcular 2% con reglas de redondeo especiales
            valor = tamano_lote * 0.02
            decimal = valor - int(valor)
            
            if decimal >= 0.50:
                tamano_muestra = math.ceil(valor)
            else:
                tamano_muestra = math.floor(valor)
        
        return tamano_muestra, 'Porcentual 2%'
    
    # Buscar en la tabla el rango correspondiente
    for rango_min, rango_max, muestra in tabla:
        if rango_min <= tamano_lote <= rango_max:
            # Si muestra es None, significa "Todas las unidades"
            if muestra is None:
                return tamano_lote, nombre
            else:
                return muestra, nombre
    
    # Si no se encuentra en la tabla, usar el último valor
    ultima_muestra = tabla[-1][2]
    if ultima_muestra is None:
        return tamano_lote, nombre
    else:
        return ultima_muestra, nombre


def calcular_muestreo(tamano_lote, especie=None, porcentaje=None, incremento_intensidad=0):
    """
    Calcula el muestreo según la especie o porcentaje especificado.
    
    Args:
        tamano_lote (int): Tamaño total del lote
        especie (str, optional): Nombre de la especie para determinar la tabla
        porcentaje (float, optional): Porcentaje de muestreo manual (solo si no se especifica especie)
        incremento_intensidad (int, optional): Incremento de intensidad (0, 20, 40). Default 0.
    
    Returns:
        dict: Diccionario con:
            - tamano_lote: Tamaño del lote
            - tipo_tabla: Tipo de tabla utilizada
            - nombre_tabla: Nombre descriptivo de la tabla
            - muestra_base: Cantidad base según tabla (antes de incremento)
            - incremento_aplicado: Porcentaje de incremento aplicado
            - muestra_final: Cantidad final de cajas a muestrear (después de incremento)
            - tamano_muestra: Alias de muestra_final (compatibilidad)
            - cajas_seleccionadas: Lista ordenada de números de caja
    """
    if tamano_lote <= 0:
        raise ValueError("El tamaño del lote debe ser mayor a 0")
    
    # Validar incremento
    if incremento_intensidad not in [0, 20, 40]:
        raise ValueError("El incremento debe ser 0, 20 o 40")
    
    # Determinar el tamaño de muestra según la especie o porcentaje
    if especie:
        tipo_tabla = obtener_tipo_tabla_muestreo(especie)
        
        # Validar que no se aplique incremento a tabla hipergeométrica
        if incremento_intensidad > 0 and tipo_tabla in ['HIPERGEOMETRICA_3', 'HIPERGEOMETRICA_6']:
            raise ValueError("No se puede aplicar incremento de intensidad a especies con tabla hipergeométrica")
        
        muestra_base, nombre_tabla = calcular_tamano_muestra_por_tabla(tamano_lote, tipo_tabla)
    elif porcentaje is not None:
        if porcentaje <= 0 or porcentaje > 100:
            raise ValueError("El porcentaje debe estar entre 0 y 100")
        muestra_base = math.ceil(tamano_lote * (porcentaje / 100))
        tipo_tabla = 'PORCENTUAL'
        nombre_tabla = f'Porcentual {porcentaje}%'
    else:
        # Default: 2%
        muestra_base = math.ceil(tamano_lote * 0.02)
        tipo_tabla = 'PORCENTUAL'
        nombre_tabla = 'Porcentual 2%'
    
    # 🚨 VALIDACIONES CRÍTICAS OFICIALES SAG-USDA 🚨
    
    # Validación 1: NUNCA exceder 49 en tabla Hipergeométrica 6%
    if tipo_tabla == 'HIPERGEOMETRICA_6' and muestra_base > 49:
        muestra_base = 49
    
    # Validación 2: NUNCA exceder el tamaño del lote
    if muestra_base > tamano_lote:
        muestra_base = tamano_lote
    
    # Validación 3: Asegurar al menos 1 unidad de muestra
    if muestra_base < 1:
        muestra_base = 1
    
    # Aplicar incremento de intensidad si corresponde
    if incremento_intensidad > 0:
        muestra_final = math.ceil(muestra_base * (1 + incremento_intensidad / 100))
        # Agregar incremento al nombre de la tabla
        nombre_tabla = f"{nombre_tabla} +{incremento_intensidad}%"
    else:
        muestra_final = muestra_base
    
    # Validación final: no exceder tamaño del lote
    if muestra_final > tamano_lote:
        muestra_final = tamano_lote
    
    # Generar números aleatorios únicos
    cajas_seleccionadas = generar_cajas_aleatorias(tamano_lote, muestra_final)
    
    return {
        'tamano_lote': tamano_lote,
        'tipo_tabla': tipo_tabla,
        'nombre_tabla': nombre_tabla,
        'muestra_base': muestra_base,
        'incremento_aplicado': incremento_intensidad,
        'muestra_final': muestra_final,
        'tamano_muestra': muestra_final,  # Compatibilidad
        'cajas_seleccionadas': cajas_seleccionadas
    }


def generar_cajas_aleatorias(tamano_lote, cantidad):
    """
    Genera una lista de números de caja aleatorios únicos.
    
    Args:
        tamano_lote (int): Rango máximo (1 a tamano_lote)
        cantidad (int): Cantidad de números a generar
    
    Returns:
        list: Lista ordenada de números únicos
    """
    if cantidad > tamano_lote:
        raise ValueError("La cantidad no puede ser mayor al tamaño del lote")
    
    # Generar números aleatorios únicos en el rango [1, tamano_lote]
    cajas = random.sample(range(1, tamano_lote + 1), cantidad)
    
    # Ordenar la lista
    cajas.sort()
    
    return cajas


def validar_datos_inspeccion(data):
    """
    Valida los datos de una inspección antes de procesarla.
    
    Args:
        data (dict): Datos de la inspección
    
    Returns:
        tuple: (es_valido: bool, errores: list)
    """
    errores = []
    
    # Validar campos requeridos
    campos_requeridos = [
        'exportador', 'establishment', 'inspector_sag', 'contraparte_sag',
        'especie', 'numero_lote', 'tamano_lote', 'tipo_muestreo',
        'tipo_despacho', 'cantidad_pallets'
    ]
    
    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            errores.append(f"El campo '{campo}' es requerido")
    
    # Validar valores numéricos
    if 'tamano_lote' in data:
        try:
            tamano_lote = int(data['tamano_lote'])
            if tamano_lote <= 0:
                errores.append("El tamaño del lote debe ser mayor a 0")
        except (ValueError, TypeError):
            errores.append("El tamaño del lote debe ser un número válido")
    
    if 'cantidad_pallets' in data:
        try:
            cantidad_pallets = int(data['cantidad_pallets'])
            if cantidad_pallets <= 0:
                errores.append("La cantidad de pallets debe ser mayor a 0")
        except (ValueError, TypeError):
            errores.append("La cantidad de pallets debe ser un número válido")
    
    return len(errores) == 0, errores


# ==================== MUESTREO POR ETAPA ====================

def validate_stage_sampling(total_pallets, boxes_per_pallet, total_boxes_lot):
    """
    Valida restricciones normativas SAG/USDA para muestreo por etapa (Cap. 3.9.2.1).
    
    Args:
        total_pallets (int): Número total de pallets
        boxes_per_pallet (list): Lista con cantidad de cajas en cada pallet
        total_boxes_lot (int): Tamaño total del lote
    
    Returns:
        tuple: (es_valido: bool, errores: list, warnings: list)
    """
    errores = []
    warnings = []
    
    # Validación básica de datos
    if not boxes_per_pallet or len(boxes_per_pallet) != total_pallets:
        errores.append(f"Debe especificar cajas para {total_pallets} pallets")
        return False, errores, warnings
    
    if sum(boxes_per_pallet) != total_boxes_lot:
        total_ingresado = sum(boxes_per_pallet)
        if total_ingresado > total_boxes_lot:
            errores.append(f"Total de cajas ingresadas ({total_ingresado}) excede el tamaño del lote ({total_boxes_lot})")
        else:
            warnings.append(f"Total de cajas ingresadas ({total_ingresado}) es menor al tamaño del lote ({total_boxes_lot})")
    
    if any(cajas <= 0 for cajas in boxes_per_pallet):
        errores.append("Todos los pallets deben tener al menos 1 caja")
        return False, errores, warnings
    
    # 1) VALIDAR MÍNIMO DE PALLETS (≥ 6)
    if total_pallets < 6:
        errores.append("El muestreo por etapa requiere mínimo 6 pallets")
        return False, errores, warnings
    
    # 2) HOMOGENEIDAD DE PALLETS (solo si total_pallets ≤ 15)
    # Para lotes > 15 pallets NO se aplica restricción de variación
    if total_pallets <= 15:
        promedio = total_boxes_lot / total_pallets
        
        for i, cajas in enumerate(boxes_per_pallet, 1):
            variacion = abs(cajas - promedio) / promedio
            if variacion > 0.30:  # 30%
                errores.append(
                    f"Pallet {i}: variación de {variacion*100:.1f}% excede el 30% permitido "
                    f"(tiene {cajas} cajas, promedio: {promedio:.1f})"
                )
    
    # 3) REGLA ESPECIAL PARA LOTES ≥ 10 PALLETS
    if total_pallets >= 10:
        promedio = total_boxes_lot / total_pallets
        umbral_60 = promedio * 0.60
        
        pallets_bajo_umbral = [
            i+1 for i, cajas in enumerate(boxes_per_pallet) 
            if cajas < umbral_60
        ]
        
        if len(pallets_bajo_umbral) > 1:
            errores.append(
                f"Solo un pallet puede tener menos del 60% del promedio ({umbral_60:.1f} cajas). "
                f"Pallets que no cumplen: {', '.join(map(str, pallets_bajo_umbral))}"
            )
    
    return len(errores) == 0, errores, warnings


def select_stage_sampling_pallets(total_pallets):
    """
    Selecciona aleatoriamente el 25% de los pallets para muestreo por etapa.
    Según manual SAG/USDA: redondeo hacia arriba (ceiling).
    
    Args:
        total_pallets (int): Número total de pallets
    
    Returns:
        list: Índices (1-based) de pallets seleccionados
    """
    # Calcular 25% con redondeo hacia arriba (ceiling) según normativa
    cantidad_pallets = max(1, math.ceil(total_pallets * 0.25))
    
    # Seleccionar aleatoriamente
    indices = random.sample(range(1, total_pallets + 1), cantidad_pallets)
    indices.sort()
    
    return indices


def distribute_samples_proportionally(boxes_per_pallet, selected_pallet_indices, total_sample_size):
    """
    Distribuye las cajas muestra proporcionalmente entre los pallets seleccionados.
    
    Args:
        boxes_per_pallet (list): Cajas en cada pallet (1-based)
        selected_pallet_indices (list): Índices de pallets seleccionados (1-based)
        total_sample_size (int): Tamaño total de la muestra
    
    Returns:
        dict: Diccionario con índice de pallet y cajas a muestrear de cada uno
    """
    # Calcular total de cajas en pallets seleccionados
    total_boxes_selected = sum(boxes_per_pallet[i-1] for i in selected_pallet_indices)
    
    # Distribuir proporcionalmente
    distribution = {}
    cajas_asignadas = 0
    
    for i, pallet_idx in enumerate(selected_pallet_indices):
        cajas_en_pallet = boxes_per_pallet[pallet_idx - 1]
        
        # Última iteración: asignar el resto
        if i == len(selected_pallet_indices) - 1:
            cajas_muestra = total_sample_size - cajas_asignadas
        else:
            # Calcular proporcionalmente
            proporcion = cajas_en_pallet / total_boxes_selected
            cajas_muestra = round(total_sample_size * proporcion)
        
        # No puede exceder el número de cajas en el pallet
        cajas_muestra = min(cajas_muestra, cajas_en_pallet)
        
        distribution[pallet_idx] = cajas_muestra
        cajas_asignadas += cajas_muestra
    
    return distribution


def generate_stage_sampling_numbers(boxes_per_pallet, selected_pallet_indices, sample_distribution):
    """
    Genera números aleatorios de cajas para muestreo por etapa.
    
    IMPORTANTE: En muestreo por etapa, la numeración es CONTINUA para los pallets seleccionados.
    Ejemplo: Si seleccionas pallets 3, 5 y 7 con 120 cajas cada uno:
    - Pallet 3 → Cajas 1-120
    - Pallet 5 → Cajas 121-240
    - Pallet 7 → Cajas 241-360
    
    Args:
        boxes_per_pallet (list): Cajas en cada pallet (1-based indexing)
        selected_pallet_indices (list): Índices de pallets seleccionados (1-based)
        sample_distribution (dict): Cantidad de cajas a muestrear por pallet
    
    Returns:
        list: Números de caja seleccionados (ordenados, numeración continua)
    """
    selected_boxes = []
    offset = 0  # Offset continuo solo para pallets seleccionados
    
    for pallet_idx in sorted(selected_pallet_indices):
        cajas_en_pallet = boxes_per_pallet[pallet_idx - 1]
        cajas_a_muestrear = sample_distribution.get(pallet_idx, 0)
        
        if cajas_a_muestrear > 0:
            # Generar números aleatorios dentro del rango continuo del pallet
            numeros_pallet = random.sample(
                range(offset + 1, offset + cajas_en_pallet + 1),
                min(cajas_a_muestrear, cajas_en_pallet)
            )
            selected_boxes.extend(numeros_pallet)
        
        # Incrementar offset solo para pallets seleccionados
        offset += cajas_en_pallet
    
    selected_boxes.sort()
    return selected_boxes
