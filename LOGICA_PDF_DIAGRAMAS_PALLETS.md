# 📊 LÓGICA COMPLETA: GENERACIÓN DE PDF DE DIAGRAMAS DE PALLETS

## 📋 ÍNDICE
1. [Función Principal de Generación PDF](#1-función-principal-generación-pdf)
2. [Función de Dibujo de Pallet](#2-función-de-dibujo-de-pallet)
3. [Estructura de Datos](#3-estructura-de-datos)
4. [Fórmulas Matemáticas](#4-fórmulas-matemáticas)
5. [CSS Necesario](#5-css-necesario)
6. [Ejemplo de Uso Completo](#6-ejemplo-de-uso-completo)

---

## 1. FUNCIÓN PRINCIPAL: GENERACIÓN PDF

```javascript
/**
 * generatePDF - Crea PDF con diagramas de pallets (2 por página, vertical)
 * 
 * ESTRUCTURA DEL PDF:
 * ┌─────────────────────────────────────────┐
 * │  PALLET 1 (ocupas ~40% de altura)       │
 * │                                         │
 * ├─────────────────────────────────────────┤  ← 8mm gap
 * │  PALLET 2 (ocupas ~40% de altura)       │
 * │                                         │
 * └─────────────────────────────────────────┘
 */
const generatePDF = async () => {
  if (!diagramData) return;

  setGeneratingPDF(true);

  try {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.width;    // 210mm (A4)
    const pageHeight = doc.internal.pageSize.height;  // 297mm (A4)
    
    const { inspection: inspData, pallets } = diagramData;

    // ========== LOOP: PROCESAR PALLETS DE 2 EN 2 ==========
    for (let i = 0; i < pallets.length; i += 2) {
      // Nueva página (excepto para los primeros 2 pallets)
      if (i > 0) {
        doc.addPage();
      }

      // Calcular espacios disponibles
      const spaceBetweenPallets = 8;  // 8mm entre pallets
      const topMargin = 5;             // 5mm arriba
      const bottomMargin = 15;         // 15mm abajo
      
      // Altura máxima por pallet: (alto total - márgenes - gap) / 2
      const maxHeightPerPallet = (pageHeight - topMargin - bottomMargin - spaceBetweenPallets) / 2;

      // ========== PALLET 1 (ARRIBA) ==========
      const palletTop = pallets[i];
      drawPalletOnPDF(doc, palletTop, inspData, pageWidth, topMargin, maxHeightPerPallet, true);

      // ========== PALLET 2 (ABAJO) - Si existe ==========
      if (i + 1 < pallets.length) {
        const palletBottom = pallets[i + 1];
        const startYBottom = topMargin + maxHeightPerPallet + spaceBetweenPallets;
        drawPalletOnPDF(doc, palletBottom, inspData, pageWidth, startYBottom, maxHeightPerPallet, false);
      }
    }

    // Guardar PDF
    doc.save(`Diagramas_Pallets_${inspData.numero_lote}.pdf`);
  } catch (error) {
    console.error('Error:', error);
    alert('Error al generar PDF: ' + error.message);
  } finally {
    setGeneratingPDF(false);
  }
};
```

---

## 2. FUNCIÓN DE DIBUJO DE PALLET

```javascript
/**
 * drawPalletOnPDF - Dibuja UN pallet completo en el PDF
 * 
 * ESTRUCTURA VISUAL:
 * ┌─────────────────────────────┐
 * │ Pallet 1                    │  ← Encabezado
 * ├─────────────────────────────┤
 * │ Lote: 001 | Especie: Mango  │  ← Info
 * ├─────────────────────────────┤
 * │ Caras: [4, 4]               │  ← Labels caras (si existen)
 * ├─────────────────────────────┤
 * │ ┌─┬─┬─┬─┐ ┌─┬─┬─┬─┐        │
 * │ │1│2│3│4│ │5│6│7│8│  Cara  │
 * │ ├─┼─┼─┼─┤ ├─┼─┼─┼─┤   A    │
 * │ │ │ │ │ │ │ │ │ │ │        │
 * │ ├─┼─┼─┼─┤ ├─┼─┼─┼─┤   +    │
 * │ │ │ │ │ │ │ │ │ │ │        │
 * │ └─┴─┴─┴─┘ └─┴─┴─┴─┘  Cara  │
 * │                       B     │
 * ├─────────────────────────────┤
 * │ ☐ Normal  ■ Muestra         │  ← Leyenda
 * └─────────────────────────────┘
 */
const drawPalletOnPDF = (doc, pallet, inspData, pageWidth, startY, maxHeight, isFirst) => {
  const { base, altura, cantidad_cajas, distribucion_caras = [] } = pallet;

  // ====== 1. ENCABEZADO ======
  const headerY = isFirst ? startY + 5 : startY + 8;
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text(`Pallet ${pallet.numero_pallet}`, pageWidth / 2, headerY, { align: 'center' });

  // Info compacta
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  let yPos = headerY + 7;
  
  if (isFirst) {
    doc.text(`Lote: ${inspData.numero_lote} | Especie: ${inspData.especie}`, 15, yPos);
    yPos += 5;
  }
  
  doc.text(`Cajas: ${pallet.inicio_caja} - ${pallet.fin_caja} | Muestra: ${pallet.total_cajas_muestra}`, 15, yPos);
  yPos += 8;

  // ====== 2. CALCULAR TAMAÑO DE CELDA ======
  // FÓRMULA: min(ancho_disponible / columnas, alto_disponible / filas, máximo)
  
  const separatorWidth = distribucion_caras.length > 1 ? 3 : 0;  // 3mm entre caras
  const numSeparators = Math.max(0, distribucion_caras.length - 1);
  const totalSeparatorWidth = numSeparators * separatorWidth;

  const availableHeight = maxHeight - (yPos - startY) - 12;
  
  const cellSize = Math.min(
    (pageWidth - 2 - totalSeparatorWidth) / base,  // Ancho: (página - márgenes) / columnas
    availableHeight / altura,                       // Alto: altura disponible / filas
    55                                              // Máximo 55mm por celda
  );

  const gridWidth = base * cellSize + totalSeparatorWidth;
  const gridHeight = altura * cellSize;
  const startX = (pageWidth - gridWidth) / 2;  // Centrar horizontalmente

  // ====== 3. FUNCIÓN AUXILIAR: Convertir columna a X ======
  // Esta función mapea número de columna → posición X en el PDF
  // Importante para pallets con múltiples caras
  const getCaraXPosition = (col) => {
    if (distribucion_caras.length === 0) {
      // Sin distribución: columnas simplemente distribuidas
      return startX + ((col - 1) * cellSize);
    }

    // Con distribución: calcular a qué cara pertenece y posición dentro
    let acumulado = 0;
    let xOffset = 0;

    for (let i = 0; i < distribucion_caras.length; i++) {
      const colsEnCara = distribucion_caras[i];
      if (col <= acumulado + colsEnCara) {
        // Encontrada la cara
        const colEnCara = col - acumulado;
        return startX + xOffset + ((colEnCara - 1) * cellSize);
      }
      acumulado += colsEnCara;
      xOffset += colsEnCara * cellSize + separatorWidth;  // Sumar separador
    }

    return startX + ((col - 1) * cellSize);
  };

  // ====== 4. DIBUJAR ETIQUETAS DE CARAS ======
  if (distribucion_caras.length > 1) {
    yPos += 3;
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(107, 114, 128);  // Gris
    
    let xOffset = startX;
    distribucion_caras.forEach((cols, index) => {
      const caraWidth = cols * cellSize;
      const caraLabel = `Cara ${String.fromCharCode(65 + index)}`;  // A, B, C...
      doc.text(caraLabel, xOffset + caraWidth / 2, yPos, { align: 'center' });
      xOffset += caraWidth + separatorWidth;
    });
    
    yPos += 4;
  }

  // ====== 5. DIBUJAR SEPARADORES ENTRE CARAS ======
  if (distribucion_caras.length > 1) {
    let xOffset = startX;
    
    for (let i = 0; i < distribucion_caras.length - 1; i++) {
      xOffset += distribucion_caras[i] * cellSize;
      
      // Línea punteada púrpura
      doc.setDrawColor(147, 51, 234);  // #9333ea
      doc.setLineWidth(0.8);
      
      const sepX = xOffset + separatorWidth / 2;
      const dashLength = 2;
      
      // Dibujar línea punteada vertical
      for (let y = yPos; y < yPos + gridHeight; y += dashLength * 2) {
        doc.line(
          sepX, 
          y, 
          sepX, 
          Math.min(y + dashLength, yPos + gridHeight)
        );
      }
      
      xOffset += separatorWidth;
    }
  }

  // ====== 6. DIBUJAR CAJAS ======
  // IMPORTANTE: Las cajas se numeran de ABAJO HACIA ARRIBA en el pallet
  // Caja 1 está en la capa inferior
  pallet.cajas.forEach((caja) => {
    // Calcular posición en grilla
    const rowFromTop = Math.ceil(caja.numero_local / base);
    const rowFromBottom = altura - rowFromTop + 1;  // FLIP: invertir Y
    const col = ((caja.numero_local - 1) % base) + 1;  // 1-based
    
    const x = getCaraXPosition(col);
    const y = yPos + (rowFromBottom - 1) * cellSize;

    // Color según si es muestra o no
    if (caja.seleccionada) {
      doc.setFillColor(59, 130, 246);      // Azul para muestra
      doc.setTextColor(255, 255, 255);     // Texto blanco
    } else {
      doc.setFillColor(255, 255, 255);     // Blanco para normal
      doc.setTextColor(55, 65, 81);        // Texto gris oscuro
    }

    // Dibujar rectángulo
    doc.setDrawColor(209, 213, 219);
    doc.setLineWidth(0.3);
    doc.rect(x, y, cellSize, cellSize, 'FD');

    // Escribir número de caja
    const fontSize = Math.max(8, Math.min(cellSize * 0.28, 16));
    doc.setFontSize(fontSize);
    doc.setFont('helvetica', 'bold');
    doc.text(
      caja.numero.toString(),
      x + cellSize / 2,
      y + cellSize / 2 + fontSize / 3.5,
      { align: 'center' }
    );
  });

  // ====== 7. LEYENDA ======
  const legendY = yPos + gridHeight + 10;
  doc.setTextColor(0, 0, 0);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7);

  // Caja normal
  doc.setFillColor(255, 255, 255);
  doc.setDrawColor(209, 213, 219);
  doc.rect(15, legendY, 5, 5, 'FD');
  doc.text('Normal', 22, legendY + 4);

  // Caja muestra
  doc.setFillColor(59, 130, 246);
  doc.rect(45, legendY, 5, 5, 'FD');
  doc.text('Muestra', 52, legendY + 4);

  // ====== 8. INFORMACIÓN ADICIONAL ======
  doc.setFontSize(6);
  doc.setTextColor(107, 114, 128);
  let infoText = `Base: ${base} | Capas: ${altura} | Total: ${cantidad_cajas}`;
  
  if (distribucion_caras.length > 1) {
    const distText = distribucion_caras.map((cols, i) => 
      `${String.fromCharCode(65 + i)}:${cols}`
    ).join(' + ');
    infoText += ` | Caras: ${distText}`;
  }
  
  doc.text(infoText, pageWidth / 2, legendY + 4, { align: 'center' });
};
```

---

## 3. ESTRUCTURA DE DATOS

### 3.1 Objeto de Entrada: `diagramData`

```javascript
{
  inspection: {
    id: 123,
    numero_lote: "LOTE-001",
    especie: "Mango",
    tipo_muestreo: "ALEATORIO"
  },
  total_pallets_mostrados: 5,
  pallets: [
    {
      numero_pallet: 1,
      base: 8,                          // Columnas por capa
      altura: 5,                        // Capas/filas
      cantidad_cajas: 28,               // Total cajas en pallet
      distribucion_caras: [4, 4],       // [Cara A: 4 cols, Cara B: 4 cols]
      inicio_caja: 1,                   // Primer número de caja
      fin_caja: 28,                     // Último número de caja
      total_cajas_muestra: 4,           // Cajas seleccionadas
      cajas: [
        {
          numero: 1,                    // Número correlativo global
          numero_local: 1,              // Posición en grilla (1 a base*altura)
          capa: 1,                      // Capa (1=abajo, altura=arriba)
          seleccionada: true            // ¿Es muestra?
        },
        {
          numero: 2,
          numero_local: 2,
          capa: 1,
          seleccionada: false
        },
        // ... más cajas hasta 28
      ]
    },
    // ... más pallets
  ]
}
```

### 3.2 Transformación de Números de Caja

```javascript
// Dados: numero_local, base
// Calcular: fila, columna

const numero_local = 5;  // Caja en la grilla
const base = 8;          // Columnas por capa

const fila = Math.ceil(numero_local / base);    // Fila de abajo hacia arriba
const columna = ((numero_local - 1) % base) + 1; // Columna de izq a derecha

// Resultado para numero_local=5, base=8:
// fila = 1 (primera capa)
// columna = 5

// Para numero_local=10, base=8:
// fila = 2 (segunda capa)
// columna = 2
```

---

## 4. FÓRMULAS MATEMÁTICAS

### 4.1 Cálculo de Capas
```javascript
// Dada cantidad total de cajas y base (cajas por capa)
const cajasTotales = 28;
const base = 8;

const capas = Math.ceil(cajasTotales / base);
// Resultado: Math.ceil(28 / 8) = Math.ceil(3.5) = 4 capas
```

### 4.2 Cálculo de Tamaño de Celda en PDF
```javascript
// Maximizar tamaño de celda manteniendo todo visible
const pageWidth = 210;           // mm (A4)
const pageHeight = 297;          // mm (A4)
const base = 8;                  // columnas
const altura = 5;                // filas
const topMargin = 5;
const bottomMargin = 15;
const separatorWidth = 3;        // mm entre caras
const numSeparators = 1;

const totalSeparatorWidth = numSeparators * separatorWidth;
const availableWidth = pageWidth - 2;  // 2mm márgenes
const availableHeight = pageHeight - topMargin - bottomMargin;

const cellSize = Math.min(
  (availableWidth - totalSeparatorWidth) / base,    // Limitado por ancho
  availableHeight / altura,                          // Limitado por alto
  55                                                 // Máximo 55mm
);

// Fórmula: min(
//   (210 - 2 - 3) / 8 = 25.875mm,
//   (297 - 5 - 15) / 5 = 55.4mm,
//   55
// ) = 25.875mm
```

### 4.3 Inversión de Coordenadas Y
```javascript
// En PDF: Y=0 está ARRIBA, aumenta hacia ABAJO
// En pallet visual: Caja 1 está ABAJO, aumenta hacia ARRIBA
// Necesario invertir:

const altura = 5;        // Total capas
const capaFromTop = 2;   // Capa contada desde arriba

const capaFromBottom = altura - capaFromTop + 1;  // = 4
// Ahora capa 2 se dibuja en posición 4 (más abajo)
```

### 4.4 Validación de Distribución
```javascript
// La suma de cols en caras DEBE IGUALAR la base
const base = 8;
const distribucion_caras = [4, 4];

const suma = distribucion_caras.reduce((sum, cols) => sum + cols, 0);
const esValido = suma === base;  // true

// Inválido:
const distribucion_invalida = [3, 4];  // suma = 7 ≠ 8 → Error
```

---

## 5. CSS NECESARIO

```css
/* ========== IMPORTACIÓN ==========*/
import { jsPDF } from 'jspdf';

/* ========== ESTILOS PARA VISUALIZACIÓN HTML (antes de PDF) ========== */
.diagrama-pallet-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pallet-grid {
  display: grid;
  gap: 2px;
  background: #f9fafb;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.box-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  min-height: 40px;
  font-weight: 700;
  user-select: none;
  transition: all 0.2s ease;
}

.box-cell.box-selected {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-color: #1d4ed8;
  color: white;
}

.cara-separator {
  background: linear-gradient(to bottom, #9333ea, #a855f7);
  border-left: 2px dashed #9333ea;
  min-height: 100%;
}

.pallet-legend {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.legend-box {
  width: 20px;
  height: 20px;
  border-radius: 3px;
  border: 1px solid #d1d5db;
}

.legend-box-normal {
  background: white;
}

.legend-box-muestra {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-color: #1d4ed8;
}
```

---

## 6. EJEMPLO DE USO COMPLETO

### 6.1 Instalación de Dependencia
```bash
npm install jspdf
```

### 6.2 Importación en Componente
```jsx
import { useState } from 'react';
import { jsPDF } from 'jspdf';

function DiagramasPalletView({ inspection, onClose }) {
  const [diagramData, setDiagramData] = useState(null);
  const [generatingPDF, setGeneratingPDF] = useState(false);

  const generatePDF = async () => {
    // [Copiar la función generatePDF completa]
  };

  const drawPalletOnPDF = (doc, pallet, inspData, pageWidth, startY, maxHeight, isFirst) => {
    // [Copiar la función drawPalletOnPDF completa]
  };

  return (
    <button onClick={generatePDF} disabled={generatingPDF}>
      {generatingPDF ? 'Generando...' : '📄 Descargar PDF'}
    </button>
  );
}

export default DiagramasPalletView;
```

### 6.3 Llamada a Backend
```javascript
const fetchDiagramData = async () => {
  try {
    const response = await fetch(
      `${API_URL}/muestreo/diagrama-pallets/${inspection.id}/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    const data = await response.json();
    setDiagramData(data.data);  // Asignar estructura completa
  } catch (err) {
    console.error('Error:', err);
  }
};
```

---

## 7. FLUJO COMPLETO

```
┌──────────────────────────────────────────────────────────────┐
│ 1. USUARIO HACE CLICK EN "DESCARGAR PDF"                     │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. fetchDiagramData()                                        │
│    - GET /api/muestreo/diagrama-pallets/{id}/               │
│    - Recibe: array de pallets con cajas numeradas           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. generatePDF()                                             │
│    - Crea instancia jsPDF                                    │
│    - Loop pallet 0-1 → página 1                             │
│    - Loop pallet 2-3 → página 2                             │
│    - etc...                                                  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. drawPalletOnPDF() (para cada pallet)                      │
│    a. Dibujar encabezado (nombre, lote, especie)           │
│    b. Calcular tamaño de celda                              │
│    c. Dibujar etiquetas de caras                            │
│    d. Dibujar separadores                                   │
│    e. Loop cajas: dibujar rectángulos + números             │
│    f. Dibujar leyenda                                       │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. doc.save("Diagramas_Pallets_LOTE.pdf")                   │
│    - Descarga archivo PDF                                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. COLORES Y ESTILOS

| Elemento | Color | Código |
|----------|-------|--------|
| Caja Normal | Blanco | #FFFFFF |
| Caja Muestra | Azul Gradiente | #3B82F6 → #2563EB |
| Borde Caja | Gris Claro | #D1D5DB |
| Separador Cara | Púrpura | #9333EA |
| Texto Gris | Gris Medio | #6B7280 |
| Fondo Grid | Gris Muy Claro | #F9FAFB |

---

## 9. PARÁMETROS AJUSTABLES

```javascript
// Espaciado PDF
const topMargin = 5;              // mm (cambiar si necesitas más/menos espacio arriba)
const bottomMargin = 15;          // mm (espacio para leyenda)
const spaceBetweenPallets = 8;    // mm (gap entre pallet 1 y 2)
const separatorWidth = 3;         // mm (ancho de línea entre caras)

// Límites de tamaño de celda
const maxCellSize = 55;           // mm (máximo tamaño por celda)

// Fuentes
const headerFontSize = 12;        // pt
const labelFontSize = 8;          // pt  
const numberFontSize = 8 - 16;    // pt (variable según cellSize)

// Configuración de línea
const gridLineWidth = 0.3;        // pt
const separatorLineWidth = 0.8;   // pt
```

---

## 10. TROUBLESHOOTING

| Problema | Causa | Solución |
|----------|-------|----------|
| Números solapados | Celda pequeña | Aumentar `maxCellSize` o reducir `base` |
| PDF muy condensado | Márgenes pequeños | Aumentar `topMargin` o `bottomMargin` |
| Caras no visibles | Separadores muy anchos | Reducir `separatorWidth` |
| Pallet cortado | Altura insuficiente | Reducir `spaceBetweenPallets` |
| Números ilegibles | Fuente pequeña | Revisar fórmula en `fontSize = Math.max(8, Math.min(...))` |

