# 🚀 QUICK START: Pasar Lógica de PDF a Otro Proyecto

## 📦 Archivos Creados

He generado 3 archivos en tu workspace que contienen TODA la lógica:

1. **LOGICA_PDF_DIAGRAMAS_PALLETS.md** - Documentación completa
2. **pdf-utils-diagramas.js** - Código frontend listo para copiar
3. **endpoint-backend-diagramas.py** - Endpoint backend con estructura

---

## ⚡ INSTALACIÓN: 5 PASOS

### Paso 1: Instalar Dependencia
```bash
npm install jspdf
```

### Paso 2: Copiar Código Frontend
Copia el contenido de `pdf-utils-diagramas.js` y pégalo en tu componente o crea un archivo de utilidades.

### Paso 3: Usar en Componente
```jsx
import { generatePDF } from './pdf-utils';

function MiComponente() {
  const handleDescargarPDF = () => {
    const diagramData = {
      inspection: { id: 1, numero_lote: "LOTE-001", especie: "Mango" },
      pallets: [ /* array de pallets */ ]
    };
    generatePDF(diagramData);
  };

  return (
    <button onClick={handleDescargarPDF}>
      📄 Descargar PDF
    </button>
  );
}
```

### Paso 4: Implementar Backend (si no existe)
Copia la función `get_pallet_diagrams` de `endpoint-backend-diagramas.py` a tu `views.py`

Registra en `urls.py`:
```python
path('diagrama-pallets/<int:inspection_id>/', views.get_pallet_diagrams, name='get-pallet-diagrams'),
```

### Paso 5: Llamar a Backend desde Frontend
```javascript
const fetchDiagramData = async (inspectionId) => {
  const response = await fetch(
    `${API_URL}/muestreo/diagrama-pallets/${inspectionId}/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const data = await response.json();
  generatePDF(data.data);
};
```

---

## 🎯 Estructura de Datos Esperada

```javascript
{
  inspection: {
    numero_lote: "LOTE-001",
    especie: "Mango"
  },
  pallets: [
    {
      numero_pallet: 1,
      base: 8,                           // Columnas por capa
      altura: 5,                         // Capas
      cantidad_cajas: 40,                // Total cajas
      distribucion_caras: [4, 4],        // [Cara A: 4, Cara B: 4]
      inicio_caja: 1,
      fin_caja: 40,
      total_cajas_muestra: 5,            // Cantidad de muestras
      cajas: [
        {
          numero: 1,                     // Número global
          numero_local: 1,               // Posición en grilla (1 a 40)
          capa: 1,                       // Capa (1=abajo, 5=arriba)
          seleccionada: true             // ¿Es muestra?
        },
        // ... 39 cajas más
      ]
    }
    // ... más pallets
  ]
}
```

---

## 🧮 Fórmulas Clave

```javascript
// Calcular capas
const capas = Math.ceil(cantidad_cajas / base);
// Ejemplo: Math.ceil(40 / 8) = 5

// Calcular fila
const fila = Math.ceil(numero_local / base);
// Ejemplo: numero_local=10, base=8 → fila=2

// Calcular columna
const columna = ((numero_local - 1) % base) + 1;
// Ejemplo: numero_local=10, base=8 → columna=2

// Invertir Y (para dibujar de abajo hacia arriba)
const yPos = altura - capa + 1;
// Ejemplo: altura=5, capa=2 → yPos=4
```

---

## 📊 Resultado Final

El PDF generado tendrá:
- ✅ 2 pallets por página (vertical)
- ✅ Grilla con cajas numeradas
- ✅ Cajas muestreadas resaltadas en azul
- ✅ Separadores entre caras (si las hay)
- ✅ Leyenda y información adicional
- ✅ Nombre de archivo: `Diagramas_Pallets_{numero_lote}.pdf`

---

## 🔧 Personalización

Ajusta estos parámetros en `generatePDF`:

```javascript
const topMargin = 5;              // mm (arriba)
const bottomMargin = 15;          // mm (abajo)
const spaceBetweenPallets = 8;    // mm (gap entre pallets)
const separatorWidth = 3;         // mm (ancho separador caras)
const maxCellSize = 55;           // mm (tamaño máximo celda)
```

---

## ❌ Troubleshooting

| Problema | Solución |
|----------|----------|
| Números solapados | Aumentar `maxCellSize` o reducir `base` |
| PDF cortado | Aumentar `bottomMargin` |
| Separadores no visibles | Reducir `separatorWidth` |
| Cajas muy pequeñas | Reducir `espacios` o `cantidad_cajas` |

---

## 📥 Resumen de Copiar y Pegar

1. **pdf-utils-diagramas.js** → Copiar a tu proyecto frontend
2. **endpoint-backend-diagramas.py** → Copiar función a tu backend
3. Importar en componente: `import { generatePDF } from './pdf-utils'`
4. Llamar con datos: `generatePDF(diagramData)`
5. Listo ✅

---

## 📱 Uso Rápido Sin Backend

Si no tienes backend, prueba con datos de prueba:

```javascript
import { generatePDF } from './pdf-utils';

// Datos de prueba
const testData = {
  inspection: {
    numero_lote: "TEST-001",
    especie: "Mango"
  },
  pallets: [
    {
      numero_pallet: 1,
      base: 8,
      altura: 5,
      cantidad_cajas: 40,
      distribucion_caras: [4, 4],
      inicio_caja: 1,
      fin_caja: 40,
      total_cajas_muestra: 5,
      cajas: Array.from({ length: 40 }, (_, i) => ({
        numero: i + 1,
        numero_local: i + 1,
        capa: Math.ceil((i + 1) / 8),
        seleccionada: i < 5  // Primeras 5 como muestra
      }))
    }
  ]
};

// Generar PDF
generatePDF(testData);
```

---

## 📖 Documentación Completa

Lee `LOGICA_PDF_DIAGRAMAS_PALLETS.md` para:
- Explicación detallada de cada función
- Fórmulas matemáticas completas
- Diagrama del flujo
- Colores y estilos
- Parámetros ajustables

---

## 📝 Notas Importantes

1. **Inversión de coordenadas**: Las cajas se numeran de **abajo hacia arriba** en el pallet
2. **Numeración continua**: En muestreo POR_ETAPA, la numeración es continua entre pallets
3. **Validación de caras**: La suma de columnas en caras DEBE igualar la base
4. **jsPDF A4**: El PDF se genera en formato A4 (210x297mm)

---

¡Listo para implementar en tu otro proyecto! 🚀
