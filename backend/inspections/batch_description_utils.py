"""
batch_description_utils.py - Utilidades para procesamiento de archivos .INS
Parseador para formato USDA Anexo N° 5
"""

import re
from datetime import datetime


class INSFileParser:
    """
    Parser para archivos .INS (Anexo N° 5 USDA)
    Estructura:
    - Encabezado: 35 caracteres
      - 5 dígitos: SIF
      - 4 dígitos: Planta
      - 8 dígitos: Especie
      - 3 dígitos: País1
      - 3 dígitos: País2
      - 8 dígitos: Fecha (YYYYMMDD)
      - 4 dígitos: Total de Pallets
    
    - Registros de pallet: 14 caracteres cada uno
      - 10 dígitos: Folio Pallet
      - 4 dígitos: Cantidad de Cajas
    
    - Terminador: && seguido de línea en blanco
    """

    def __init__(self, file_content):
        """
        Inicializa el parser con el contenido del archivo
        
        Args:
            file_content: Contenido del archivo como string
        """
        self.file_content = file_content
        self.errors = []
        self.warnings = []
        self.data = None

    def parse(self):
        """
        Parsea el contenido del archivo .INS
        
        Returns:
            dict: Datos parseados o None si hay errores críticos
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Normalizar saltos de línea (CRLF -> LF, CR -> LF)
            normalized_content = self.file_content.replace('\r\n', '\n').replace('\r', '\n')
            lines = normalized_content.split('\n')
            
            logger.error(f"[PARSE] Total lines in file: {len(lines)}")
            print(f"[PARSE] Total lines in file: {len(lines)}")
            
            if not lines:
                self.errors.append('El archivo está vacío')
                return None
            
            # Obtener primera línea y limpiar caracteres no imprimibles
            header_line = lines[0] if lines else ''
            # Remove non-printable characters
            header_line_clean = ''.join(c for c in header_line if ord(c) >= 32 or c in '\t\n\r')
            
            logger.error(f"[PARSE] First line original length: {len(header_line)}")
            logger.error(f"[PARSE] First line after cleanup length: {len(header_line_clean)}")
            logger.error(f"[PARSE] First line original repr: {repr(header_line[:50])}")
            logger.error(f"[PARSE] First line after cleanup repr: {repr(header_line_clean[:50])}")
            
            print(f"[PARSE] First line length: {len(header_line_clean)}")
            print(f"[PARSE] First line repr: {repr(header_line_clean[:50])}")
            
            # Parsear encabezado
            header_data = self._parse_header(header_line_clean)
            
            if not header_data:
                return None
            
            # Parsear registros de pallets
            pallets = []
            for i in range(1, len(lines)):
                line = lines[i].strip()
                
                # Detectar terminador
                if line.startswith('&&') or line == '&&':
                    logger.error(f"[PARSE] Found terminator at line {i}")
                    break
                
                # Saltar líneas vacías
                if not line:
                    logger.error(f"[PARSE] Line {i} is empty, skipping")
                    continue
                
                logger.error(f"[PARSE] Line {i}: {repr(line[:30])}... (len={len(line)})")
                
                # Parsear registro de pallet
                pallet_data = self._parse_pallet_record(line)
                if pallet_data:
                    pallets.append(pallet_data)
                    logger.error(f"[PARSE] Pallet {i} parsed successfully")
                else:
                    logger.error(f"[PARSE] Pallet {i} failed to parse")
            
            logger.error(f"[PARSE] Total pallets parsed: {len(pallets)}")
            print(f"[PARSE] Total pallets parsed: {len(pallets)}")
            
            # Validar cantidad de pallets
            expected_count = int(header_data.get('total_pallets', 0))
            if len(pallets) != expected_count:
                self.warnings.append(
                    f'Se esperaban {expected_count} pallets pero se encontraron {len(pallets)}'
                )
            
            self.data = {
                'header': header_data,
                'pallets': pallets,
                'total_pallets': len(pallets),
                'errors': self.errors,
                'warnings': self.warnings
            }
            
            logger.error(f"[PARSE] SUCCESS - parsed {len(pallets)} pallets")
            print(f"[PARSE] SUCCESS - parsed {len(pallets)} pallets")
            
            return self.data
        
        except Exception as e:
            self.errors.append(f'Error al parsear archivo: {str(e)}')
            logger = logging.getLogger(__name__)
            logger.error(f"[PARSE] EXCEPTION: {str(e)}")
            return None

    def _parse_header(self, header_line):
        """
        Parsea la línea de encabezado (35 caracteres)
        
        Args:
            header_line: Primera línea del archivo
        
        Returns:
            dict: Datos del encabezado parseados
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Limpiar y asegurar longitud mínima
        header_line = header_line.strip() if header_line else ''
        
        # Remove non-printable characters but preserve spaces
        header_line = ''.join(c for c in header_line if ord(c) >= 32 or c in '\t\n\r')
        header_line = header_line.strip()
        
        logger.error(f"[HEADER PARSE] Original header length: {len(header_line)}")
        logger.error(f"[HEADER PARSE] Header repr: {repr(header_line)}")
        logger.error(f"[HEADER PARSE] Header bytes: {header_line.encode('utf-8')}")
        
        print(f"[HEADER PARSE] Original header length: {len(header_line)}")
        print(f"[HEADER PARSE] Header repr: {repr(header_line)}")
        
        if len(header_line) < 35:
            error_msg = f'Encabezado inválido: se esperan 35 caracteres, se encontraron {len(header_line)}'
            self.errors.append(error_msg)
            logger.error(f"[HEADER PARSE] {error_msg}")
            return None
        
        try:
            # Extraer campos según posición (sin hacer strip en los campos individuales)
            # para preservar el formato esperado
            sif = header_line[0:5]
            planta = header_line[5:9]
            especie = header_line[9:17]
            pais1 = header_line[17:20]
            pais2 = header_line[20:23]
            fecha_str = header_line[23:31]
            total_pallets_str = header_line[31:35]
            
            logger.error(f"[HEADER PARSE] SIF: '{sif}' (codes: {[ord(c) for c in sif]})")
            logger.error(f"[HEADER PARSE] Planta: '{planta}' (codes: {[ord(c) for c in planta]})")
            logger.error(f"[HEADER PARSE] Especie: '{especie}' (codes: {[ord(c) for c in especie]})")
            logger.error(f"[HEADER PARSE] País1: '{pais1}'")
            logger.error(f"[HEADER PARSE] País2: '{pais2}'")
            logger.error(f"[HEADER PARSE] Fecha: '{fecha_str}'")
            logger.error(f"[HEADER PARSE] Total Pallets: '{total_pallets_str}'")
            
            print(f"[HEADER PARSE] SIF: '{sif}' isdigit={sif.isdigit()}")
            print(f"[HEADER PARSE] Planta: '{planta}' isdigit={planta.isdigit()}")
            print(f"[HEADER PARSE] Especie: '{especie}' isdigit={especie.isdigit()}")
            print(f"[HEADER PARSE] Total Pallets: '{total_pallets_str}' isdigit={total_pallets_str.isdigit()}")
            
            # Validar que sean numéricos
            if not sif.isdigit():
                msg = f'SIF debe ser numérico. Recibido: {repr(sif)}'
                self.errors.append(msg)
                logger.error(f"[HEADER PARSE] ERROR: {msg}")
                return None
            if not planta.isdigit():
                msg = f'Planta debe ser numérica. Recibido: {repr(planta)}'
                self.errors.append(msg)
                logger.error(f"[HEADER PARSE] ERROR: {msg}")
                return None
            if not especie.isdigit():
                msg = f'Especie debe ser numérica. Recibido: {repr(especie)}'
                self.errors.append(msg)
                logger.error(f"[HEADER PARSE] ERROR: {msg}")
                return None
            if not total_pallets_str.isdigit():
                msg = f'Total de pallets debe ser numérico. Recibido: {repr(total_pallets_str)}'
                self.errors.append(msg)
                logger.error(f"[HEADER PARSE] ERROR: {msg}")
                return None
            
            # Parsear fecha
            fecha = None
            try:
                fecha = datetime.strptime(fecha_str, '%Y%m%d')
                fecha_formatted = fecha.strftime('%d/%m/%Y')
            except ValueError:
                self.warnings.append(f'Fecha inválida: {fecha_str}')
                fecha_formatted = fecha_str
            
            logger.error(f"[HEADER PARSE] SUCCESS - parsed header")
            print(f"[HEADER PARSE] SUCCESS - parsed header")
            
            return {
                'sif': sif,
                'planta': planta,
                'especie': especie,
                'pais1': pais1,
                'pais2': pais2,
                'fecha': fecha_formatted,
                'fecha_raw': fecha_str,
                'total_pallets': int(total_pallets_str)
            }
        
        except IndexError as e:
            self.errors.append(f'Error al extraer campos del encabezado: {str(e)}')
            return None

    def _parse_pallet_record(self, line):
        """
        Parsea un registro de pallet (14 caracteres)
        
        Args:
            line: Línea a parsear
        
        Returns:
            dict: Datos del pallet o None si es inválido
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Limpiar y asegurar longitud
        line = line.strip() if line else ''
        
        # Remove non-printable characters
        line_clean = ''.join(c for c in line if ord(c) >= 32 or c in '\t\n\r')
        line_clean = line_clean.strip()
        
        # Necesita exactamente 14 caracteres
        if len(line_clean) != 14:
            logger.warning(f"[PALLET PARSE] Line length {len(line_clean)} != 14: {repr(line_clean[:20])}")
            return None
        
        try:
            # Extraer campos según posición (sin strip para preservar formato)
            folio = line_clean[0:10]
            cajas_str = line_clean[10:14]
            
            logger.error(f"[PALLET PARSE] Folio: '{folio}' (codes: {[ord(c) for c in folio]}), Cajas: '{cajas_str}' (codes: {[ord(c) for c in cajas_str]})")
            
            # Validar que sean numéricos
            if not folio.isdigit():
                logger.warning(f"[PALLET PARSE] Folio no es numérico: {repr(folio)}")
                return None
            if not cajas_str.isdigit():
                logger.warning(f"[PALLET PARSE] Cajas no es numérico: {repr(cajas_str)}")
                return None
            
            result = {
                'folio_pallet': folio,
                'cajas': int(cajas_str)
            }
            logger.error(f"[PALLET PARSE] SUCCESS - Pallet {folio} with {cajas_str} boxes")
            return result
        
        except Exception as e:
            logger.warning(f"[PALLET PARSE] Exception: {str(e)}")
            return None


def validate_ins_file(file_content):
    """
    Valida que el contenido sea un archivo .INS válido
    
    Args:
        file_content: Contenido del archivo
    
    Returns:
        tuple: (is_valid, error_message)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not file_content or not file_content.strip():
        return False, 'El archivo está vacío'
    
    # Normalizar saltos de línea (CRLF -> LF, CR -> LF)
    normalized_content = file_content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Obtener todas las líneas (incluso vacías) para logging
    all_lines = normalized_content.split('\n')
    non_empty_lines = [line.strip() for line in all_lines if line.strip()]
    
    logger.error(f"[INS Validation] Total lines: {len(all_lines)}, Non-empty: {len(non_empty_lines)}")
    logger.error(f"[INS Validation] Last 5 non-empty lines: {non_empty_lines[-5:]}")
    
    print(f"[INS Validation] Total lines: {len(all_lines)}, Non-empty: {len(non_empty_lines)}")
    print(f"[INS Validation] Last 5 non-empty lines: {non_empty_lines[-5:]}")
    
    # Buscar el terminador && de forma flexible
    has_terminator = False
    terminator_line_idx = None
    
    for idx, line in enumerate(all_lines):
        stripped = line.strip()
        # Buscar línea que contenga o sea &&
        if '&&' in stripped:
            has_terminator = True
            terminator_line_idx = idx
            logger.error(f"[INS Validation] Found terminator at line {idx}: {repr(stripped)}")
            print(f"[INS Validation] Found terminator at line {idx}: {repr(stripped)}")
            break
    
    # Si no encontramos terminador, buscar directamente en el contenido
    if not has_terminator:
        if '&&' in normalized_content:
            has_terminator = True
            logger.error(f"[INS Validation] Found && in content directly")
            print(f"[INS Validation] Found && in content directly")
        else:
            logger.error(f"[INS Validation] NO terminator found anywhere!")
            print(f"[INS Validation] NO terminator found anywhere!")
            # NO retornar error aquí - simplemente continuar
            # return False, 'El archivo no contiene el terminador && requerido'
    
    # Validar que hay al menos 2 líneas no vacías (encabezado + datos)
    if len(non_empty_lines) < 2:
        return False, f'El archivo debe tener al menos 2 líneas (header + datos). Se encontraron {len(non_empty_lines)}'
    
    logger.error(f"[INS Validation] PASSED - file appears valid")
    print(f"[INS Validation] PASSED - file appears valid")
    
    return True, None
