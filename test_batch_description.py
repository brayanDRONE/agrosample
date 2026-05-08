"""
test_batch_description.py - Test del módulo batch_description
"""

from backend.batch_description_utils import INSFileParser

# Crear un archivo .INS de prueba
# Formato: 35 caracteres de encabezado + registros de 14 caracteres cada uno
# Encabezado (35 chars): SIF(5) + Planta(4) + Especie(8) + País1(3) + País2(3) + Fecha(8) + Total(4)
# Registros (14 chars): Folio(10) + Cajas(4)

header = "00123"      # SIF
header += "0405"      # Planta
header += "05678902"  # Especie
header += "012"       # País 1
header += "202"       # País 2
header += "20230115"  # Fecha YYYYMMDD
header += "0003"      # Total de pallets = 3

# Crear 3 registros de pallets
pallet1 = "0000000001" + "0010"  # Folio 1, 10 cajas
pallet2 = "0000000002" + "0020"  # Folio 2, 20 cajas
pallet3 = "0000000003" + "0030"  # Folio 3, 30 cajas

test_ins_content = header + "\n" + pallet1 + "\n" + pallet2 + "\n" + pallet3 + "\n&&\n"

def test_parser():
    parser = INSFileParser(test_ins_content)
    result = parser.parse()
    
    print("=" * 60)
    print("TEST: Parser de archivos .INS")
    print("=" * 60)
    
    if result:
        print("✓ Parsing exitoso")
        print("\nDatos del encabezado:")
        header = result['header']
        print(f"  SIF: {header.get('sif')}")
        print(f"  Planta: {header.get('planta')}")
        print(f"  Especie: {header.get('especie')}")
        print(f"  País 1: {header.get('pais1')}")
        print(f"  País 2: {header.get('pais2')}")
        print(f"  Fecha: {header.get('fecha')}")
        print(f"  Total de Pallets: {header.get('total_pallets')}")
        
        print(f"\nPallets detectados: {len(result['pallets'])}")
        for idx, pallet in enumerate(result['pallets'], 1):
            print(f"  {idx}. Folio: {pallet['folio_pallet']}, Cajas: {pallet['cajas']}")
        
        if result['warnings']:
            print(f"\nAdvertencias:")
            for warning in result['warnings']:
                print(f"  ⚠ {warning}")
    else:
        print("✗ Error al parsear")
        for error in parser.errors:
            print(f"  ✗ {error}")
    
    print("=" * 60)

if __name__ == '__main__':
    test_parser()
