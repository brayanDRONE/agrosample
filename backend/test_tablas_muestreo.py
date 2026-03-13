"""
Script de prueba para verificar las tablas de muestreo oficiales SAG-USDA.
"""
import sys
import os
import django

# Agregar el directorio backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from inspections.utils import calcular_muestreo, obtener_tipo_tabla_muestreo

print("=" * 80)
print("PRUEBA DE TABLAS OFICIALES SAG-USDA")
print("=" * 80)

# ==================== HIPERGEOMÉTRICA 3% ====================
print("\n" + "=" * 80)
print("HIPERGEOMÉTRICA 3% - Damasco (sin frío)")
print("=" * 80)

pruebas_h3 = [
    (50, 50, "≤900 todas"),
    (900, 900, "≤900 todas"),
    (901, 63, "901-1500"),
    (1500, 63, "901-1500"),
    (1501, 90, "1501-4000"),
    (4000, 90, "1501-4000"),
    (5000, 94, "4001-10000"),
    (12000, 96, "10001-15000"),
    (18000, 98, "15001-20000"),
    (25000, 99, ">20000"),
]

for lote, esperado, rango in pruebas_h3:
    resultado = calcular_muestreo(lote, especie='Damasco')
    ok = "OK" if resultado['tamano_muestra'] == esperado else "FAIL"
    print(f"{ok} Lote: {lote:>6} → Muestra: {resultado['tamano_muestra']:>3} (esperado: {esperado:>3}) [{rango}]")

# ==================== HIPERGEOMÉTRICA 6% ====================
print("\n" + "=" * 80)
print("HIPERGEOMÉTRICA 6% - Durazno, Ciruela, etc.")
print("LIMITE MAXIMO: 49 unidades")
print("=" * 80)

pruebas_h6 = [
    (10, 10, "≤37 todas"),
    (37, 37, "≤37 todas"),
    (38, 37, "38-78"),
    (78, 37, "38-78"),
    (79, 38, "79-88"),
    (100, 39, "89-117"),
    (120, 40, "118-140"),
    (150, 41, "141-157"),
    (200, 43, "176-207"),
    (300, 45, "258-335"),
    (400, 46, "336-425"),
    (500, 47, "426-850"),
    (700, 47, "426-850"),
    (1000, 48, "851-2250"),
    (2250, 48, "851-2250"),
    (2251, 49, ">2250 LÍMITE"),
    (5000, 49, ">2250 LÍMITE"),
    (10000, 49, ">2250 LÍMITE"),
    (50000, 49, ">2250 LÍMITE"),
]

for lote, esperado, rango in pruebas_h6:
    resultado = calcular_muestreo(lote, especie='Durazno')
    ok = "OK" if resultado['tamano_muestra'] == esperado else "FAIL"
    print(f"{ok} Lote: {lote:>6} → Muestra: {resultado['tamano_muestra']:>3} (esperado: {esperado:>3}) [{rango}]")

# Verificar que NUNCA excede 49
print("\nVALIDACION CRITICA: Verificando limite de 49")
lotes_grandes = [3000, 10000, 50000, 100000, 500000]
for lote in lotes_grandes:
    resultado = calcular_muestreo(lote, especie='Ciruela')
    ok = "OK" if resultado['tamano_muestra'] <= 49 else "FAIL X"
    print(f"{ok} Lote: {lote:>7} → Muestra: {resultado['tamano_muestra']:>3}")

# ==================== BIOMÉTRICA ====================
print("\n" + "=" * 80)
print("BIOMÉTRICA - Manzana, Pera, Kiwi, etc.")
print("=" * 80)

pruebas_bio = [
    (10, 10, "≤30 todas"),
    (30, 30, "≤30 todas"),
    (31, 30, "31-2000"),
    (100, 30, "31-2000"),
    (2000, 30, "31-2000"),
    (2001, 50, "2001-10000"),
    (5000, 50, "2001-10000"),
    (10000, 50, "2001-10000"),
    (10001, 100, ">10000"),
    (50000, 100, ">10000"),
]

for lote, esperado, rango in pruebas_bio:
    resultado = calcular_muestreo(lote, especie='Manzana')
    ok = "OK" if resultado['tamano_muestra'] == esperado else "FAIL"
    print(f"{ok} Lote: {lote:>6} → Muestra: {resultado['tamano_muestra']:>3} (esperado: {esperado:>3}) [{rango}]")

# ==================== PORCENTUAL 2% ====================
print("\n" + "=" * 80)
print("PORCENTUAL 2% - Otras especies (ej: Arándano)")
print("Reglas: ≤100 → 2, >100 → 2% con redondeo especial")
print("=" * 80)

pruebas_porc = [
    (50, 2, "≤100"),
    (100, 2, "≤100"),
    (101, 2, "2% floor"),
    (124, 2, "2% floor (2.48)"),
    (125, 3, "2% ceil (2.50)"),
    (150, 3, "2% ceil (3.00)"),
    (200, 4, "2% ceil (4.00)"),
    (1000, 20, "2% ceil (20.00)"),
]

for lote, esperado, regla in pruebas_porc:
    resultado = calcular_muestreo(lote, especie='Arándano')
    ok = "OK" if resultado['tamano_muestra'] == esperado else "FAIL"
    valor = lote * 0.02
    print(f"{ok} Lote: {lote:>5} → Muestra: {resultado['tamano_muestra']:>3} (esperado: {esperado:>3}) [calc: {valor:.2f}, {regla}]")

print("\n" + "=" * 80)
print("TODAS LAS PRUEBAS COMPLETADAS")
print("=" * 80)
