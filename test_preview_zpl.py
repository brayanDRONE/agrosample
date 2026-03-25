import os
import sys
import requests

# Agregar directorio actual al path para importar
sys.path.insert(0, r'c:\agrosample')

from zebra_print_service import build_zpl_small_label_5x2

zpl_code = build_zpl_small_label_5x2("100", 731, 795, "PROPAL")

print("ZPL CODE:")
print(zpl_code)

# El ZPL tiene ^PW830 (4.08 pulgadas) y ^LL200 (1 pulgada) a 203 DPI (8 dpmm)
url = 'http://api.labelary.com/v1/printers/8dpmm/labels/4x1/0/'
headers = {'Accept': 'image/png'}

response = requests.post(url, data=zpl_code, headers=headers)

output_path = r'C:\Users\brayan\.gemini\antigravity\brain\8ddffab8-c77b-40bd-b30b-73478ab9a508\label_preview_vertical.png'

if response.status_code == 200:
    with open(output_path, 'wb') as f:
        f.write(response.content)
    print(f"✅ Preview guardado exitosamente en: {output_path}")
else:
    print(f"❌ Error {response.status_code}: {response.text}")
