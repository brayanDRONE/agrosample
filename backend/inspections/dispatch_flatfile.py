"""
Generación de archivo plano de despacho en formato Multipuerto (42 campos).
Formato: 42 campos separados por ; en una sola línea.

Mapeo correcto de los 42 campos (basado en archivos Multipuerto funcionales):
 1. codigo_exportadora       (6604)
 2. nro_planilla             (4)
 3. codigo_puerto_embarque   (56)
 4. codigo_puerto_destino    (107)
 5. codigo_producto          (2624)  <- CODIGOPRODUCTO de EXPV_PRODUCTOS_ESPECIE_TC
 6. tipo_transporte          (5)
 7. patente_camion           (CBXV55)
 8. patente_carro            (0064794) - SIEMPRE es patente_carro, no guia_despacho
 9. fecha_despacho           (2026-05-29)
10. nro_pallet_ubicacion    (123)
11. cantidad_kg             (1968.0000)
12. codigo_especie          (4)
13. codigo_variedad         (4)
14. codigo_establecimiento  (1378)
15. numero_contenedor       (HLBU970121-7)
16. codigo_tipo_envase      (1)
17. codigo_csg              (07,03,08)
18-23. muestreo_1-6         (vacíos)
24. cantidad_envases        (2)
25. codigo_exportadora_alt  (12)  <- SIEMPRE es 12
26. total_kg_decimales      (10207,1)
27. ubicacion_sello         (1)
28. campo_28                (vacío)
29. numero_sellos           (49)
30-31. campos_30-31         (vacíos)
32. tipo_produccion         (1)
33. transgenico             (1)
34. codigo_agencia_aduana   (PTXT92)
35. campo_35                (vacío)
36. tratado                 (0)
37. campo_37                (vacío)
38. codigo_establecimiento_2 (1378)
39. reservado               (DELEGADO)
40. codigo_pais_destino     (23)
41. codigo_pais_puerto_destino (120877)
42. codigo_exportadora_final (90388)
"""
from datetime import datetime


def _clean_field(value):
    """Normalize a field value for flat file output."""
    if value is None:
        return ''
    s = str(value).strip()
    # Only remove semicolons (field separator), preserve commas and dots (decimals/list separators)
    s = s.replace(';', '').replace('\r', ' ').replace('\n', ' ')
    return s


def build_dispatch_flat_file(payload):
    """
    Build a Multipuerto flat file with 42 fields in the correct order.
    
    Args:
        payload: dict with keys matching the 42-field structure:
            - codigo_exportadora: str
            - nro_planilla: str
            - codigo_puerto_embarque: str
            - codigo_puerto_destino: str
            - tipo_transporte: str
            - tipo_puerto_descarga: str
            - patente_camion: str
            - patente_carro: str (always the truck plate, NOT guia_despacho)
            - guia_despacho: str (informational only, not used for field 8)
            - fecha_despacho: str (YYYY-MM-DD)
            - nro_pallet_ubicacion: str
            - cantidad_kg: str (format: #.0000)
            - codigo_especie: str
            - codigo_variedad: str
            - codigo_establecimiento: str
            - numero_contenedor: str
            - codigo_tipo_envase: str
            - codigo_csg: str (comma-separated: 07,03,08)
            - muestreo_1 to 6: str (usually empty)
            - cantidad_envases: str
            - codigo_exportadora_alt: str
            - total_kg_decimales: str (format: #,# with comma as decimal separator)
            - ubicacion_sello: str
            - numero_sellos: str
            - tipo_produccion: str (1 or 0)
            - transgenico: str (1 or 0)
            - codigo_agencia_aduana: str
            - tratado: str (0 or 1)
            - codigo_establecimiento_2: str
            - codigo_pais_destino: str
            - codigo_pais_puerto_destino: str
            - codigo_exportadora_final: str
    
    Returns:
        tuple: (filename, content)
            - filename: str, format "Multipuerto_{planilla_id}_{timestamp}.txt"
            - content: str, single line with 42 semicolon-separated fields
    """
    # Field 1: codigo_exportadora
    f1 = _clean_field(payload.get('codigo_exportadora', ''))
    
    # Field 2: nro_planilla
    f2 = _clean_field(payload.get('nro_planilla', ''))
    
    # Field 3: codigo_puerto_embarque
    f3 = _clean_field(payload.get('codigo_puerto_embarque', ''))
    
    # Field 4: codigo_puerto_destino
    f4 = _clean_field(payload.get('codigo_puerto_destino', ''))
    
    # Field 5: codigo_producto (CODIGOPRODUCTO de EXPV_PRODUCTOS_ESPECIE_TC)
    f5 = _clean_field(payload.get('codigo_producto', ''))
    
    # Field 6: tipo_transporte
    f6 = _clean_field(payload.get('tipo_transporte', ''))
    
    # Field 7: patente_camion
    f7 = _clean_field(payload.get('patente_camion', ''))
    
    # Field 8: patente_carro (SIEMPRE es patente_carro, no guia_despacho)
    f8 = _clean_field(payload.get('patente_carro', ''))
    
    # Field 9: fecha_despacho
    f9 = _clean_field(payload.get('fecha_despacho', ''))
    
    # Field 10: nro_pallet_ubicacion
    f10 = _clean_field(payload.get('nro_pallet_ubicacion', ''))
    
    # Field 11: cantidad_kg
    f11 = _clean_field(payload.get('cantidad_kg', ''))
    
    # Field 12: codigo_especie
    f12 = _clean_field(payload.get('codigo_especie', ''))
    
    # Field 13: codigo_variedad
    f13 = _clean_field(payload.get('codigo_variedad', ''))
    
    # Field 14: codigo_establecimiento
    f14 = _clean_field(payload.get('codigo_establecimiento', ''))
    
    # Field 15: numero_contenedor
    f15 = _clean_field(payload.get('numero_contenedor', ''))
    
    # Field 16: codigo_tipo_envase
    f16 = _clean_field(payload.get('codigo_tipo_envase', ''))
    
    # Field 17: codigo_csg
    f17 = _clean_field(payload.get('codigo_csg', ''))
    
    # Fields 18-23: muestreo_1 to 6 (usually empty)
    f18 = _clean_field(payload.get('muestreo_1', ''))
    f19 = _clean_field(payload.get('muestreo_2', ''))
    f20 = _clean_field(payload.get('muestreo_3', ''))
    f21 = _clean_field(payload.get('muestreo_4', ''))
    f22 = _clean_field(payload.get('muestreo_5', ''))
    f23 = _clean_field(payload.get('muestreo_6', ''))
    
    # Field 24: cantidad_envases
    f24 = _clean_field(payload.get('cantidad_envases', ''))
    
    # Field 25: codigo_exportadora_alt (siempre 12 en el formato Multipuerto)
    f25 = _clean_field(payload.get('codigo_exportadora_alt', '12')) or '12'
    
    # Field 26: total_kg_decimales
    f26 = _clean_field(payload.get('total_kg_decimales', ''))
    
    # Field 27: ubicacion_sello
    f27 = _clean_field(payload.get('ubicacion_sello', ''))
    
    # Field 28: empty
    f28 = _clean_field(payload.get('campo_28', ''))
    
    # Field 29: numero_sellos
    f29 = _clean_field(payload.get('numero_sellos', ''))
    
    # Fields 30-31: empty
    f30 = _clean_field(payload.get('campo_30', ''))
    f31 = _clean_field(payload.get('campo_31', ''))
    
    # Field 32: tipo_produccion
    f32 = _clean_field(payload.get('tipo_produccion', ''))
    
    # Field 33: transgenico
    f33 = _clean_field(payload.get('transgenico', ''))
    
    # Field 34: codigo_agencia_aduana
    f34 = _clean_field(payload.get('codigo_agencia_aduana', ''))
    
    # Field 35: empty
    f35 = _clean_field(payload.get('campo_35', ''))
    
    # Field 36: tratado
    f36 = _clean_field(payload.get('tratado', ''))
    
    # Field 37: empty
    f37 = _clean_field(payload.get('campo_37', ''))
    
    # Field 38: codigo_establecimiento_2
    f38 = _clean_field(payload.get('codigo_establecimiento_2', ''))
    
    # Field 39: reservado
    f39 = _clean_field(payload.get('reservado', 'DELEGADO'))
    
    # Field 40: codigo_pais_destino
    f40 = _clean_field(payload.get('codigo_pais_destino', ''))
    
    # Field 41: codigo_pais_puerto_destino
    f41 = _clean_field(payload.get('codigo_pais_puerto_destino', ''))
    
    # Field 42: codigo_exportadora_final
    f42 = _clean_field(payload.get('codigo_exportadora_final', ''))
    
    # Build the 42-field record
    fields = [f1, f2, f3, f4, f5, f6, f7, f8, f9, f10,
              f11, f12, f13, f14, f15, f16, f17, f18, f19, f20,
              f21, f22, f23, f24, f25, f26, f27, f28, f29, f30,
              f31, f32, f33, f34, f35, f36, f37, f38, f39, f40,
              f41, f42]
    
    # Build filename with planilla_id and timestamp
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    filename = f"Multipuerto_{f2}_{timestamp}.txt"
    
    # Join fields with semicolon (single line)
    content = ";".join(fields)
    
    return filename, content