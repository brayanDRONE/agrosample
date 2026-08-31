# Guía de Pruebas - Nuevo Sistema de Mapeo Multipuerto 42 Campos

## ✅ Cambios Completados

### 1. **Estructura de 42 campos corregida**
   - Campos ahora en orden exacto del formato Multipuerto real
   - Implementada lógica de guia_despacho → 00000 cuando está vacía
   - Separación correcta de patente camión/carro

### 2. **Extracción mejorada del PDF**
   - Soporte para multiline en regex patterns
   - Mejor manejo de caracteres especiales y acentos

### 3. **Mapeo de códigos**
   - Nuevas funciones de lookup para:
     - Puertos (VALPARAISO → 56)
     - Especies/Variedades (NARANJAS/FUKUMOTO → códigos)
     - Exportadoras (RUT → código)
     - Países (GUATEMALA → 23)
     - Tipo de transporte (CONTENEDOR → 5)
   - Tipo de envase (Cajas → 4, según catálogo SAG)

---

## 📋 Próximos Pasos para Probar

### Paso 1: Tener un PDF SAG válido
- Necesitas: PDF de Planilla SAG 4 con texto seleccionable
- Ubicación: Cargarlo en el dashboard o API

### Paso 2: Prueba con el endpoint
```bash
POST http://localhost:5173/api/dispatch-flatfile/generate-from-pdf/
Content-Type: multipart/form-data
File: [pdf_sag_planilla.pdf]
```

### Paso 3: Validar respuesta
**Esperado: Archivo TXT con 42 campos separados por `;`**

Ejemplo:
```
90388;1666;56;107;5;3;FTVC60;00000;2026-05-29;123;1968.0000;4;4;1378;HLBU970121-7;1;07,03,08;;;;;;2;12;10207,1;1;;49;;;1;1;PTXT92;;0;;1378;DELEGADO;23;120877;90388
```

### Paso 4: Validar campos clave
Cuando guia_despacho = vacío:
- ✓ Campo 8 = 00000 (no patente_carro)

Cuando guia_despacho = "123456":
- ✓ Campo 8 = 123456

---

## 🔍 Validación Manual

### Desglose de los 42 campos (ejemplo esperado):

```
 1. 90388            ← código_exportadora
 2. 1666             ← nro_planilla
 3. 56               ← código_puerto_embarque (VALPARAISO)
 4. 107              ← código_puerto_destino (PUERTO QUETZAL)
 5. 5                ← tipo_transporte (CONTENEDOR)
 6. 3                ← tipo_puerto_descarga
 7. FTVC60           ← patente_camion
 8. 00000            ← patente_carro (guia_despacho vacío → 00000)
 9. 2026-05-29       ← fecha_despacho
10. 123              ← nro_pallet_ubicacion
11. 24000.0          ← cantidad_kg
12. 4                ← codigo_especie (NARANJAS)
13. 4                ← codigo_variedad (FUKUMOTO)
14. 1378             ← codigo_establecimiento
15. HLBU970121-7     ← numero_contenedor
16. 4                ← codigo_tipo_envase (Cajas)
17. 07,03,08         ← codigo_csg (tratamiento)
18-23. (vacíos)      ← muestreo_1-6
24. 1600             ← cantidad_envases
25. 90388            ← codigo_exportadora_alt
26. 24000.0          ← total_kg_decimales
27. 1                ← ubicacion_sello
28. (vacío)          ← campo_28
29. 49               ← numero_sellos
30-31. (vacíos)      ← campos_30-31
32. 1                ← tipo_produccion (1=Convencional)
33. 0                ← transgenico (0=NO)
34. AG. DE           ← codigo_agencia_aduana (truncado a 10 chars)
35. (vacío)          ← campo_35
36. 0                ← tratado (0=NO)
37. (vacío)          ← campo_37
38. 1378             ← codigo_establecimiento_2
39. DELEGADO         ← reservado
40. 23               ← codigo_pais_destino (GUATEMALA)
41. (vacío)          ← codigo_pais_puerto_destino (TODO: necesita lookup)
42. 90388            ← codigo_exportadora_final
```

---

## ⚠️ Casos Especiales

### Caso 1: Guía de Despacho Vacía
```
guia_despacho: ""
patente_carro: "0064794"
→ Campo 8 será: "00000"  ✓ (guia_despacho tiene prioridad)
```

### Caso 2: Tipo de Producción
```
tipo_produccion: "Convencional"     → Campo 32 = "1"
tipo_produccion: "Orgánico"         → Campo 32 = "2"
```

### Caso 3: Transgénico
```
transgenico: "NO"     → Campo 33 = "0"
transgenico: "SI"     → Campo 33 = "1"
```

### Caso 4: Tratado
```
tratado: False     → Campo 36 = "0"
tratado: True      → Campo 36 = "1"
```

---

## 🐛 Troubleshooting

### Error: "multiline argument not recognized"
- ✅ **Solucionado**: Se agregó soporte para `multiline=True` en `_extract_value()`

### Error: "Could not extract codes from XML"
- Verificar que archivos XML existen en `data/`:
  - EXPORTADORA.xml
  - EXPV_SUB_PUERTO.xml
  - EXPV_PRODUCTOS_ESPECIE_TC.xml

### Campo vacío cuando se espera valor
- Verificar función lookup correspondiente en `code_lookups.py`
- Campos con lookup: puertos, especies, variedades, exportadora, país

---

## 📝 Archivos Modificados

| Archivo | Cambio | Estado |
|---------|--------|--------|
| `backend/inspections/dispatch_flatfile.py` | Reescrito completo con 42 campos correctos | ✅ |
| `backend/inspections/planilla_parser.py` | Actualizado mapeo a multipuerto | ✅ |
| `backend/inspections/code_lookups.py` | NUEVO - Funciones de lookup | ✅ |

---

## 🚀 Próximo: Integración en Dashboard

Cuando los códigos de lookup estén validados con datos reales:
1. Crear admin para cargar códigos correctos en base de datos
2. Reemplazar lecturas XML con queries a BD
3. Agregar validación de códigos faltantes en PDF upload

---

## 📞 Soporte

Si surge error:
1. Revisar logs del backend: `python manage.py runserver` en terminal
2. Ejecutar script de validación: `python validate_changes.py`
3. Verificar XML files en carpeta `data/`
