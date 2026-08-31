#!/usr/bin/env python3
"""
Script de diagnóstico: prueba el parser de planilla PDF.
Uso: python diagnostico_pdf.py ruta/al/archivo.pdf
"""
import sys
import io
# Forzar UTF-8 en la salida para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from inspections.planilla_parser import parse_planilla_pdf, map_planilla_to_multipuerto
from inspections.dispatch_flatfile import build_dispatch_flat_file

if len(sys.argv) < 2:
    print("Uso: python diagnostico_pdf.py <ruta_al_pdf>")
    print("\nPDFs disponibles en media/batch_descriptions:")
    for p in Path("media/batch_descriptions").glob("*.pdf"):
        print(f"  {p}")
    sys.exit(1)

pdf_path = sys.argv[1]
print(f"\n{'='*60}")
print(f"DIAGNÓSTICO: {pdf_path}")
print(f"{'='*60}")

# --- PASO 1: Extraer texto crudo del PDF ---
print("\n[1] Extrayendo texto del PDF...")
try:
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        print(f"    Páginas: {len(pdf.pages)}")
        page = pdf.pages[0]
        raw_text = page.extract_text()
        if raw_text:
            print(f"    Texto extraído ({len(raw_text)} chars). Primeras 500 líneas:")
            print("-" * 40)
            print(raw_text[:1500])
            print("-" * 40)
        else:
            print("    ❌ No se pudo extraer texto. El PDF puede estar escaneado (imagen).")
            sys.exit(1)
except Exception as e:
    print(f"    ❌ Error con pdfplumber: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# --- PASO 2: Parsear campos ---
print("\n[2] Parseando campos...")
try:
    data = parse_planilla_pdf(pdf_path)
    print(f"    ✓ {len(data)} campos extraídos:")
    for k, v in data.items():
        val_repr = repr(v)[:70]
        status = "✓" if v and v != '' and v != [] else "⚠ vacío"
        print(f"    {status}  {k}: {val_repr}")
except Exception as e:
    print(f"    ❌ Error al parsear: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# --- PASO 3: Mapear a Multipuerto ---
print("\n[3] Mapeando a formato Multipuerto...")
try:
    payload = map_planilla_to_multipuerto(data)
    print(f"    ✓ {len(payload)} campos mapeados")
except Exception as e:
    print(f"    ❌ Error al mapear: {e}")
    sys.exit(1)

# --- PASO 4: Generar archivo plano ---
print("\n[4] Generando archivo plano...")
try:
    filename, content = build_dispatch_flat_file(payload)
    fields = content.split(';')
    print(f"    ✓ Archivo: {filename}")
    print(f"    ✓ Campos en output: {len(fields)}/42")
    print(f"\n    Contenido completo:")
    print(f"    {content}")
    print(f"\n    Guardado en: output_{filename}")
    with open(f"output_{filename}", "w", encoding="utf-8") as f:
        f.write(content)
except Exception as e:
    print(f"    ❌ Error al generar: {e}")
    sys.exit(1)

print(f"\n{'='*60}")
print("✅ DIAGNÓSTICO COMPLETO - Todo funcionó correctamente")
print(f"{'='*60}\n")
