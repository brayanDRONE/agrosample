/**
 * DiagramasPalletView - Vista para mostrar diagramas de todos los pallets
 * 
 * Obtiene los datos de diagramas desde el backend y renderiza
 * un DiagramaPallet por cada pallet que debe mostrarse.
 */

import { useState, useEffect } from 'react';
import { jsPDF } from 'jspdf';
import DiagramaPallet from './DiagramaPallet';
import ConfiguracionDiagramaView from './ConfiguracionDiagramaView';
import './DiagramasPalletView.css';

function DiagramasPalletView({ inspection, selectedNumbers = [], onClose }) {
  const [diagramData, setDiagramData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generatingPDF, setGeneratingPDF] = useState(false);
  const [requiresConfiguration, setRequiresConfiguration] = useState(false);
  const [selectedPalletIndex, setSelectedPalletIndex] = useState(0); // Vista detallada

  const totalPallets = diagramData?.pallets?.length || 0;
  const detailPallets = diagramData?.pallets?.slice(selectedPalletIndex, selectedPalletIndex + 2) || [];

  useEffect(() => {
    fetchDiagramData();
  }, [inspection.id, selectedNumbers]);

  const applyUserSelectionToDiagramData = (rawData) => {
    if (!rawData || !Array.isArray(rawData.pallets)) return rawData;

    const validUserNumbers = (selectedNumbers || [])
      .map((n) => parseInt(n, 10))
      .filter((n) => Number.isFinite(n) && n > 0);

    if (validUserNumbers.length === 0) {
      return rawData;
    }

    const selectedSet = new Set(validUserNumbers);

    const updatedPallets = rawData.pallets.map((pallet) => {
      const updatedCajas = (pallet.cajas || []).map((caja) => ({
        ...caja,
        seleccionada: selectedSet.has(caja.numero)
      }));

      const cajasMuestra = updatedCajas
        .filter((caja) => caja.seleccionada)
        .map((caja) => caja.numero);

      return {
        ...pallet,
        cajas: updatedCajas,
        cajas_muestra: cajasMuestra,
        total_cajas_muestra: cajasMuestra.length
      };
    });

    return {
      ...rawData,
      pallets: updatedPallets
    };
  };

  const fetchDiagramData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      
      const headers = {
        'Content-Type': 'application/json'
      };
      
      // Solo agregar Authorization si existe token
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(
        `${API_URL}/muestreo/diagrama-pallets/${inspection.id}/`,
        {
          headers
        }
      );

      const data = await response.json();

      // Verificar primero si requiere configuración (antes de verificar response.ok)
      if (data.requires_configuration) {
        console.info('ℹ️ Configuración de pallets requerida - Mostrando modal de configuración');
        setRequiresConfiguration(true);
        setLoading(false);
        return;
      }

      if (!response.ok) {
        throw new Error(data.message || 'Error al obtener datos de diagrama');
      }

      if (!data.success) {
        throw new Error(data.message);
      }

      setDiagramData(applyUserSelectionToDiagramData(data.data));
      setRequiresConfiguration(false);
    } catch (err) {
      console.error('Error fetching diagram data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigurationCompleted = () => {
    // Después de configurar, volver a cargar los datos del diagrama
    setRequiresConfiguration(false);
    fetchDiagramData();
  };

  const generatePDF = () => {
    if (!diagramData) return;

    setGeneratingPDF(true);

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
      console.log(`PDF generado: ${filename}`);
    } catch (error) {
      console.error('Error generando PDF:', error);
      alert('Error al generar PDF: ' + error.message);
    } finally {
      setGeneratingPDF(false);
    }
  };

  const drawPalletOnPDF = (doc, pallet, inspData, pageWidth, startY, maxHeight, isFirst) => {
    const { base, altura, cantidad_cajas, distribucion_caras = [] } = pallet;

    // Encabezado del pallet con más espacio si no es el primero
    const headerY = isFirst ? startY + 5 : startY + 8;
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text(`Pallet ${pallet.numero_pallet}`, pageWidth / 2, headerY, { align: 'center' });

    // Información compacta
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    let yPos = headerY + 7;
    
    if (isFirst) {
      doc.text(`Lote: ${inspData.numero_lote} | Especie: ${inspData.especie}`, 15, yPos);
      yPos += 5;
    }
    
    doc.text(`Cajas: ${pallet.inicio_caja} - ${pallet.fin_caja} | Muestra: ${pallet.total_cajas_muestra}`, 15, yPos);
    yPos += 8;

    // Configuración de separadores entre caras
    const separatorWidth = distribucion_caras.length > 1 ? 3 : 0;
    const numSeparators = Math.max(0, distribucion_caras.length - 1);
    const totalSeparatorWidth = numSeparators * separatorWidth;

    // Calcular tamaño de celda para que quepa en el espacio disponible
    const availableHeight = maxHeight - (yPos - startY) - 12;
    const cellSize = Math.min(
      (pageWidth - 2 - totalSeparatorWidth) / base,
      availableHeight / altura,
      55
    );

    const gridWidth = base * cellSize + totalSeparatorWidth;
    const gridHeight = altura * cellSize;
    const startX = (pageWidth - gridWidth) / 2;

    // Función auxiliar para obtener info de cara y calcular X con separadores
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

    // Dibujar etiquetas de caras si hay distribución
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

    // Dibujar separadores verticales entre caras
    if (distribucion_caras.length > 1) {
      let xOffset = startX;
      
      for (let i = 0; i < distribucion_caras.length - 1; i++) {
        xOffset += distribucion_caras[i] * cellSize;

        // Línea punteada vertical
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

    // Dibujar cada caja (invertido: caja 1 abajo)
    pallet.cajas.forEach((caja) => {
      const rowFromTop = Math.ceil(caja.numero_local / base);
      const rowFromBottom = altura - rowFromTop + 1;
      const col = ((caja.numero_local - 1) % base) + 1; // 1-based
      
      const x = getCaraXPosition(col);
      const y = yPos + (rowFromBottom - 1) * cellSize;

      // Color según si es muestra o no
      if (caja.seleccionada) {
        doc.setFillColor(59, 130, 246); // Azul para muestra
        doc.setTextColor(255, 255, 255); // Texto blanco
      } else {
        doc.setFillColor(255, 255, 255); // Blanco para normal
        doc.setTextColor(55, 65, 81); // Texto gris oscuro
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

    // Leyenda compacta
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

  if (loading) {
    return (
      <div className="diagramas-overlay">
        <div className="diagramas-modal loading-modal">
          <div className="spinner-large"></div>
          <p>Cargando diagramas de pallets...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="diagramas-overlay">
        <div className="diagramas-modal error-modal">
          <div className="error-icon">⚠</div>
          <h2>Error al cargar diagramas</h2>
          <p>{error}</p>
          <button className="btn btn-secondary" onClick={onClose}>
            Cerrar
          </button>
        </div>
      </div>
    );
  }

  // Si requiere configuración, mostrar modal de configuración
  if (requiresConfiguration) {
    return (
      <ConfiguracionDiagramaView
        inspection={inspection}
        onClose={onClose}
        onConfigured={handleConfigurationCompleted}
      />
    );
  }

  if (!diagramData) return null;

  return (
    <div className="diagramas-overlay">
      <div className="diagramas-modal">
        {/* Header */}
        <div className="diagramas-header">
          <div className="header-left">
            <h2>Diagramas de Pallets</h2>
            <p className="diagramas-subtitle">
              Lote: {diagramData.inspection.numero_lote} - {diagramData.inspection.especie} ({diagramData.total_pallets_mostrados} Pallets)
            </p>
          </div>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        {/* Botones de acción */}
        <div className="diagramas-actions">
          <button
            className="btn btn-success"
            onClick={generatePDF}
            disabled={generatingPDF}
          >
            {generatingPDF ? (
              <>
                <span className="spinner"></span>
                Generando PDF...
              </>
            ) : (
              <>
                📄 Descargar PDF
              </>
            )}
          </button>
        </div>

        {/* Lista de diagramas */}
        <div className="diagramas-content">
          {/* Vista Detallada - Pallet Grande */}
          <div className="diagramas-detail-section">
            <div className="detail-header">
              <span className="counter">
                Mostrando pallets {selectedPalletIndex + 1}
                {selectedPalletIndex + 1 < totalPallets ? ` y ${selectedPalletIndex + 2}` : ''}
                {' '}de {totalPallets}
              </span>
              <div className="detail-controls">
                <button 
                  className="btn-detail-nav btn-detail-nav-prev"
                  onClick={() => setSelectedPalletIndex((prev) => Math.max(0, prev - 2))}
                  disabled={selectedPalletIndex === 0}
                >
                  ← Anterior
                </button>
                <button 
                  className="btn-detail-nav btn-detail-nav-next"
                  onClick={() => setSelectedPalletIndex((prev) => Math.min(Math.max(0, totalPallets - 1), prev + 2))}
                  disabled={selectedPalletIndex >= totalPallets - 2}
                >
                  Siguiente →
                </button>
              </div>
            </div>
            
            <div className="detail-viewer detail-viewer-grid">
              {detailPallets.map((pallet) => (
                <DiagramaPallet
                  key={`detail-${pallet.numero_pallet}`}
                  palletData={pallet}
                  basePallet={pallet.base}
                  alturaPallet={pallet.altura}
                  distribucionCaras={pallet.distribucion_caras || []}
                />
              ))}
            </div>
          </div>

          {/* Miniaturas - Grid Responsivo */}
          <div className="diagramas-thumbnails">
            <p className="thumbnails-label">Todos los Pallets:</p>
            <div className="thumbnails-grid">
              {diagramData.pallets.map((pallet, index) => (
                <button
                  key={`thumb-${pallet.numero_pallet}`}
                  className={`thumbnail-item ${selectedPalletIndex === index ? 'active' : ''}`}
                  onClick={() => setSelectedPalletIndex(index)}
                  title={`Pallet ${pallet.numero_pallet}`}
                >
                  <div className="thumbnail-number">P{pallet.numero_pallet}</div>
                  <div className="thumbnail-info">
                    <span className="thumbnail-cajas">{pallet.fin_caja - pallet.inicio_caja + 1}</span>
                    <span className="thumbnail-label">cajas</span>
                    <span className="thumbnail-muestra">{pallet.total_cajas_muestra} muestras</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="diagramas-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}

export default DiagramasPalletView;
