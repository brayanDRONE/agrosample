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
        try:
            lines = self.file_content.split('\n')
            
            if not lines:
                self.errors.append('El archivo está vacío')
                return None
            
            # Parsear encabezado
            header_line = lines[0] if lines else ''
            header_data = self._parse_header(header_line)
            
            if not header_data:
                return None
            
            # Parsear registros de pallets
            pallets = []
            for i in range(1, len(lines)):
                line = lines[i].strip()
                
                # Detectar terminador
                if line.startswith('&&') or line == '&&':
                    break
                
                # Saltar líneas vacías
                if not line:
                    continue
                
                # Parsear registro de pallet
                pallet_data = self._parse_pallet_record(line)
                if pallet_data:
                    pallets.append(pallet_data)
            
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
            
            return self.data
        
        except Exception as e:
            self.errors.append(f'Error al parsear archivo: {str(e)}')
            return None

    def _parse_header(self, header_line):
        """
        Parsea la línea de encabezado (35 caracteres)
        
        Args:
            header_line: Primera línea del archivo
        
        Returns:
            dict: Datos del encabezado parseados
        """
        # Limpiar y asegurar longitud mínima
        header_line = header_line.strip() if header_line else ''
        
        if len(header_line) < 35:
            self.errors.append(
                f'Encabezado inválido: se esperan 35 caracteres, se encontraron {len(header_line)}'
            )
            return None
        
        try:
            # Extraer campos según posición
            sif = header_line[0:5].strip()
            planta = header_line[5:9].strip()
            especie = header_line[9:17].strip()
            pais1 = header_line[17:20].strip()
            pais2 = header_line[20:23].strip()
            fecha_str = header_line[23:31].strip()
            total_pallets_str = header_line[31:35].strip()
            
            # Validar que sean numéricos
            if not sif.isdigit():
                self.errors.append('SIF debe ser numérico')
                return None
            if not planta.isdigit():
                self.errors.append('Planta debe ser numérica')
                return None
            if not especie.isdigit():
                self.errors.append('Especie debe ser numérica')
                return None
            if not total_pallets_str.isdigit():
                self.errors.append('Total de pallets debe ser numérico')
                return None
            
            # Parsear fecha
            fecha = None
            try:
                fecha = datetime.strptime(fecha_str, '%Y%m%d')
                fecha_formatted = fecha.strftime('%d/%m/%Y')
            except ValueError:
                self.warnings.append(f'Fecha inválida: {fecha_str}')
                fecha_formatted = fecha_str
            
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
        # Limpiar y asegurar longitud
        line = line.strip() if line else ''
        
        # Necesita al menos 14 caracteres
        if len(line) < 14:
            # Puede ser una línea parcial, intentar parsear lo disponible
            pass
        
        try:
            # Extraer campos
            folio = line[0:10].strip()
            cajas_str = line[10:14].strip()
            
            # Validar que sean numéricos
            if not folio.isdigit():
                self.warnings.append(f'Folio inválido: {folio}')
                return None
            if not cajas_str.isdigit():
                self.warnings.append(f'Cantidad de cajas inválida: {cajas_str}')
                return None
            
            return {
                'folio_pallet': folio,
                'cajas': int(cajas_str)
            }
        
        except Exception as e:
            self.warnings.append(f'Error al parsear registro de pallet: {str(e)}')
            return None


def validate_ins_file(file_content):
    """
    Valida que el contenido sea un archivo .INS válido
    
    Args:
        file_content: Contenido del archivo
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file_content:
        return False, 'El archivo está vacío'
    
    lines = file_content.strip().split('\n')
    
    if len(lines) < 2:
        return False, 'El archivo debe tener al menos 2 líneas'
    
    # Verificar que tenga terminador
    has_terminator = False
    for line in lines:
        if line.strip().startswith('&&'):
            has_terminator = True
            break
    
    if not has_terminator:
        return False, 'El archivo no contiene el terminador && requerido'
    
    return True, None
