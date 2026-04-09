import sys
import requests

sys.path.insert(0, r'c:\agrosample')

from zebra_print_service import build_zpl_bixolon_4x5, BIXOLON_TOTAL_W, BIXOLON_H

zpl_code = build_zpl_bixolon_4x5("2024-001", "42", "43", "MUESTRA USDA")

print("ZPL CODE:")
print(zpl_code)
print()

# Labelary API: 8dpmm = 203 DPI
# Dimensiones: ancho_pulgadas x alto_pulgadas
# BIXOLON_TOTAL_W dots / 8 dpmm / mm_per_inch... o simplemente dots/203*inch
# Ancho total: ~826 dots / 203 = ~4.07"
# Alto: ~319 dots / 203 = ~1.57"
ancho_in = round(BIXOLON_TOTAL_W / 203, 2)
alto_in  = round(BIXOLON_H / 203, 2)

label_size_str = f"{ancho_in}x{alto_in}"
print(f"Dimensiones para Labelary: {label_size_str} pulgadas")
print(f"  Ancho total tira: {BIXOLON_TOTAL_W} dots ({ancho_in:.2f}\")")
print(f"  Alto etiqueta:    {BIXOLON_H} dots ({alto_in:.2f}\")")

url = f'http://api.labelary.com/v1/printers/8dpmm/labels/{label_size_str}/0/'
headers = {'Accept': 'image/png'}

response = requests.post(url, data=zpl_code.encode('utf-8'), headers=headers)

output_path = r'c:\agrosample\preview_label_bixolon_5x4.png'

if response.status_code == 200:
    with open(output_path, 'wb') as f:
        f.write(response.content)
    print(f"\n✅ Preview guardado en: {output_path}")
else:
    print(f"\n❌ Error {response.status_code}: {response.text}")
