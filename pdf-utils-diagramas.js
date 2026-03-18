/**
 * ============================================================================
 * LÓGICA PURA: GENERACIÓN DE PDF DE DIAGRAMAS DE PALLETS
 * ============================================================================
 * 
 * Copia y pega estas funciones directamente en tu componente React
 * Única dependencia: npm install jspdf
 * 
 * USO:
 * const diagramData = { inspection, pallets };
 * generatePDF(diagramData);
 */

import { jsPDF } from 'jspdf';

/**
 * ============================================================================
 * FUNCIÓN PRINCIPAL: GENERAR PDF
 * ============================================================================
 */
export const generatePDF = (diagramData) => {
  if (!diagramData) {
    console.error('No hay datos para generar PDF');
    return;
  }

  try {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.width;
    const pageHeight = doc.internal.pageSize.height;
    
    const { inspection: inspData, pallets } = diagramData;

    // Procesar pallets de 2 en 2 (2 por página)
    for (let i = 0; i < pallets.length; i += 2) {
      // Nueva página (excepto para los primeros 2)
      if (i > 0) {
        doc.addPage();
      }

      // Espacios
      const spaceBetweenPallets = 8;
      const topMargin = 5;
      const bottomMargin = 15;
      const maxHeightPerPallet = (pageHeight - topMargin - bottomMargin - spaceBetweenPallets) / 2;

      // PALLET 1 (ARRIBA)
      const palletTop = pallets[i];
      drawPalletOnPDF(doc, palletTop, inspData, pageWidth, topMargin, maxHeightPerPallet, true);

      // PALLET 2 (ABAJO) - Si existe
      if (i + 1 < pallets.length) {
        const palletBottom = pallets[i + 1];
        const startYBottom = topMargin + maxHeightPerPallet + spaceBetweenPallets;
        drawPalletOnPDF(doc, palletBottom, inspData, pageWidth, startYBottom, maxHeightPerPallet, false);
      }
    }

    // Guardar archivo
    const filename = `Diagramas_Pallets_${inspData.numero_lote}.pdf`;
    doc.save(filename);
    console.log(`✓ PDF generado: ${filename}`);

  } catch (error) {
    console.error('Error generando PDF:', error);
    alert('Error al generar PDF: ' + error.message);
  }
};

/**
 * ============================================================================
 * FUNCIÓN: DIBUJAR UN PALLET EN PDF
 * ============================================================================
 */
export const drawPalletOnPDF = (
  doc, 
  pallet, 
  inspData, 
  pageWidth, 
  startY, 
  maxHeight, 
  isFirst
) => {
  const { base, altura, cantidad_cajas, distribucion_caras = [] } = pallet;

  // ========== ENCABEZADO ==========
  const headerY = isFirst ? startY + 5 : startY + 8;
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text(`Pallet ${pallet.numero_pallet}`, pageWidth / 2, headerY, { align: 'center' });

  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  let yPos = headerY + 7;
  
  if (isFirst) {
    doc.text(`Lote: ${inspData.numero_lote} | Especie: ${inspData.especie}`, 15, yPos);
    yPos += 5;
  }
  
  doc.text(
    `Cajas: ${pallet.inicio_caja} - ${pallet.fin_caja} | Muestra: ${pallet.total_cajas_muestra}`,
    15,
    yPos
  );
  yPos += 8;

  // ========== CALCULAR TAMAÑO DE CELDA ==========
  const separatorWidth = distribucion_caras.length > 1 ? 3 : 0;
  const numSeparators = Math.max(0, distribucion_caras.length - 1);
  const totalSeparatorWidth = numSeparators * separatorWidth;

  const availableHeight = maxHeight - (yPos - startY) - 12;
  
  const cellSize = Math.min(
    (pageWidth - 2 - totalSeparatorWidth) / base,
    availableHeight / altura,
    55
  );

  const gridWidth = base * cellSize + totalSeparatorWidth;
  const gridHeight = altura * cellSize;
  const startX = (pageWidth - gridWidth) / 2;

  // ========== FUNCIÓN: Posición X por columna ==========
  const getCaraXPosition = (col) => {
    if (distribucion_caras.length === 0) {
      return startX + ((col - 1) * cellSize);
    }

    let acumulado = 0;
    let xOffset = 0;

    for (let i = 0; i < distribucion_caras.length; i++) {
      const colsEnCara = distribucion_caras[i];
      if (col <= acumulado + colsEnCara) {
        const colEnCara = col - acumulado;
        return startX + xOffset + ((colEnCara - 1) * cellSize);
      }
      acumulado += colsEnCara;
      xOffset += colsEnCara * cellSize + separatorWidth;
    }

    return startX + ((col - 1) * cellSize);
  };

  // ========== ETIQUETAS DE CARAS ==========
  if (distribucion_caras.length > 1) {
    yPos += 3;
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(107, 114, 128);
    
    let xOffset = startX;
    distribucion_caras.forEach((cols, index) => {
      const caraWidth = cols * cellSize;
      const caraLabel = `Cara ${String.fromCharCode(65 + index)}`;
      doc.text(caraLabel, xOffset + caraWidth / 2, yPos, { align: 'center' });
      xOffset += caraWidth + separatorWidth;
    });
    
    yPos += 4;
  }

  // ========== SEPARADORES ENTRE CARAS ==========
  if (distribucion_caras.length > 1) {
    let xOffset = startX;
    
    for (let i = 0; i < distribucion_caras.length - 1; i++) {
      xOffset += distribucion_caras[i] * cellSize;
      
      doc.setDrawColor(147, 51, 234);
      doc.setLineWidth(0.8);
      
      const sepX = xOffset + separatorWidth / 2;
      const dashLength = 2;
      
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

  // ========== DIBUJAR CAJAS ==========
  pallet.cajas.forEach((caja) => {
    const rowFromTop = Math.ceil(caja.numero_local / base);
    const rowFromBottom = altura - rowFromTop + 1;  // FLIP Y
    const col = ((caja.numero_local - 1) % base) + 1;
    
    const x = getCaraXPosition(col);
    const y = yPos + (rowFromBottom - 1) * cellSize;

    // Color según selección
    if (caja.seleccionada) {
      doc.setFillColor(59, 130, 246);
      doc.setTextColor(255, 255, 255);
    } else {
      doc.setFillColor(255, 255, 255);
      doc.setTextColor(55, 65, 81);
    }

    // Dibujar celda
    doc.setDrawColor(209, 213, 219);
    doc.setLineWidth(0.3);
    doc.rect(x, y, cellSize, cellSize, 'FD');

    // Número
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

  // ========== LEYENDA ==========
  const legendY = yPos + gridHeight + 10;
  doc.setTextColor(0, 0, 0);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7);

  // Normal
  doc.setFillColor(255, 255, 255);
  doc.setDrawColor(209, 213, 219);
  doc.rect(15, legendY, 5, 5, 'FD');
  doc.text('Normal', 22, legendY + 4);

  // Muestra
  doc.setFillColor(59, 130, 246);
  doc.rect(45, legendY, 5, 5, 'FD');
  doc.text('Muestra', 52, legendY + 4);

  // Info adicional
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

/**
 * ============================================================================
 * FUNCIONES AUXILIARES
 * ============================================================================
 */

/**
 * Calcula el número de capas en un pallet
 */
export const calcularCapas = (cantidad_cajas, base) => {
  return Math.ceil(cantidad_cajas / base);
};

/**
 * Calcula la fila de una caja (desde abajo = 1)
 */
export const calcularFila = (numero_local, base) => {
  return Math.ceil(numero_local / base);
};

/**
 * Calcula la columna de una caja (1-based)
 */
export const calcularColumna = (numero_local, base) => {
  return ((numero_local - 1) % base) + 1;
};

/**
 * Valida que la distribución de caras sea correcta
 */
export const validarDistribucion = (base, distribucion_caras) => {
  const suma = distribucion_caras.reduce((sum, cols) => sum + cols, 0);
  return suma === base;
};

/**
 * ============================================================================
 * EJEMPLO DE USO EN COMPONENTE REACT
 * ============================================================================
 */

/*
import { useState } from 'react';
import { generatePDF } from './pdf-utils';

function DiagramasPalletView({ inspection }) {
  const [diagramData, setDiagramData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Obtener datos del backend
  const fetchDiagramData = async () => {
    try {
      const response = await fetch(
        `/api/muestreo/diagrama-pallets/${inspection.id}/`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const data = await response.json();
      setDiagramData(data.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePDF = () => {
    if (diagramData) {
      generatePDF(diagramData);
    }
  };

  return (
    <div>
      {loading ? (
        <p>Cargando...</p>
      ) : (
        <button onClick={handleGeneratePDF}>
          📄 Descargar PDF
        </button>
      )}
    </div>
  );
}

export default DiagramasPalletView;
*/

/**
 * ============================================================================
 * ESTRUCTURA DE DATOS ESPERADA
 * ============================================================================
 */

/*
{
  inspection: {
    id: 123,
    numero_lote: "LOTE-001",
    especie: "Mango"
  },
  pallets: [
    {
      numero_pallet: 1,
      base: 8,
      altura: 5,
      cantidad_cajas: 28,
      distribucion_caras: [4, 4],
      inicio_caja: 1,
      fin_caja: 28,
      total_cajas_muestra: 4,
      cajas: [
        {
          numero: 1,
          numero_local: 1,
          capa: 1,
          seleccionada: true
        },
        {
          numero: 2,
          numero_local: 2,
          capa: 1,
          seleccionada: false
        },
        // ... más cajas
      ]
    }
    // ... más pallets
  ]
}
*/
