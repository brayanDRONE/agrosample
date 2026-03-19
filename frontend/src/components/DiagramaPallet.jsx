/**
 * DiagramaPallet - Componente para visualizar un pallet con sus cajas
 * 
 * Muestra una grilla visual de un pallet con numeración correlativa
 * y resalta las cajas seleccionadas para muestreo.
 */

import { useEffect, useRef, useState } from 'react';
import './DiagramaPallet.css';

function DiagramaPallet({ palletData, basePallet, alturaPallet, distribucionCaras = [], inspectionNumber = 'N/A' }) {
  const [selectedBox, setSelectedBox] = useState(null);
  const [boxCellSize, setBoxCellSize] = useState(26);
  const gridWrapperRef = useRef(null);

  useEffect(() => {
    const updateBoxCellSize = () => {
      if (!gridWrapperRef.current || !basePallet) return;

      const wrapperWidth = gridWrapperRef.current.clientWidth;
      const separatorCount = Math.max(distribucionCaras.length - 1, 0);
      const totalColumns = basePallet + separatorCount;
      const gapPx = 2;
      const separatorWidthPx = 8;

      // Base * size + separators + gaps = ancho disponible
      const availableForCells = wrapperWidth
        - (separatorCount * separatorWidthPx)
        - ((totalColumns - 1) * gapPx)
        - 20; // padding interno horizontal de la grilla

      const nextSize = Math.floor(availableForCells / basePallet);
      const boundedSize = Math.max(20, Math.min(nextSize, 74));

      if (Number.isFinite(boundedSize)) {
        setBoxCellSize(boundedSize);
      }
    };

    updateBoxCellSize();

    const resizeObserver = new ResizeObserver(() => {
      updateBoxCellSize();
    });

    if (gridWrapperRef.current) {
      resizeObserver.observe(gridWrapperRef.current);
    }

    window.addEventListener('resize', updateBoxCellSize);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', updateBoxCellSize);
    };
  }, [basePallet, distribucionCaras]);

  const handleBoxClick = (caja) => {
    setSelectedBox(selectedBox?.numero === caja.numero ? null : caja);
  };

  const handleCloseTooltip = () => {
    setSelectedBox(null);
  };

  /**
   * Calcula en qué cara está una columna y su posición dentro de esa cara
   */
  const getCaraInfo = (col) => {
    if (distribucionCaras.length === 0) {
      return { caraIndex: 0, colEnCara: col, offsetCols: 0 };
    }

    let acumulado = 0;
    let offsetCols = 0; // Cantidad de columnas separadoras antes de esta

    for (let i = 0; i < distribucionCaras.length; i++) {
      const colsEnCara = distribucionCaras[i];
      if (col <= acumulado + colsEnCara) {
        return {
          caraIndex: i,
          colEnCara: col - acumulado,
          offsetCols: i // Cada cara tiene un separador antes (excepto la primera)
        };
      }
      acumulado += colsEnCara;
    }

    return { caraIndex: 0, colEnCara: col, offsetCols: 0 };
  };

  /**
   * Genera el template de columnas para CSS Grid incluyendo separadores
   */
  const getGridTemplateColumns = () => {
    if (distribucionCaras.length <= 1) {
      return `repeat(${basePallet}, var(--box-cell-size))`;
    }

    // Generar template con separadores entre caras
    const parts = [];
    distribucionCaras.forEach((cols, index) => {
      if (index > 0) {
        parts.push('8px'); // Separador de 8px
      }
      parts.push(`repeat(${cols}, var(--box-cell-size))`);
    });

    return parts.join(' ');
  };

  /**
   * Renderiza las etiquetas de caras si hay distribución
   */
  const renderCaraLabels = () => {
    if (distribucionCaras.length <= 1) return null;

    let startCol = 1;
    const labels = [];

    distribucionCaras.forEach((cols, index) => {
      const endCol = startCol + cols - 1 + index; // +index por los separadores

      labels.push(
        <div
          key={index}
          className="cara-label-overlay"
          style={{
            gridColumn: `${startCol} / ${endCol + 1}`,
            gridRow: 1
          }}
        >
          Cara {String.fromCharCode(65 + index)}
        </div>
      );

      startCol = endCol + 2; // +1 para siguiente cara, +1 para separador
    });

    return labels;
  };

  return (
    <div className="diagrama-pallet-container">
      {/* Encabezado del pallet */}
      <div className="pallet-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <div>
            <h3>Pallet {palletData.numero_pallet}</h3>
            <div className="pallet-info">
              <span className="info-badge">
                Cajas: {palletData.inicio_caja} - {palletData.fin_caja}
              </span>
              <span className={`info-badge ${palletData.total_cajas_muestra > 0 ? 'badge-muestra' : 'badge-vacio'}`}>
                {palletData.total_cajas_muestra > 0 
                  ? `${palletData.total_cajas_muestra} muestra${palletData.total_cajas_muestra > 1 ? 's' : ''}`
                  : 'Sin muestras'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Grilla de cajas */}
      <div className="pallet-grid-wrapper" ref={gridWrapperRef}>
        {distribucionCaras.length > 1 && (
          <div className="caras-labels">
            {distribucionCaras.map((cols, index) => (
              <div key={index} className="cara-label-top" style={{ flex: cols }}>
                Cara {String.fromCharCode(65 + index)}
              </div>
            ))}
          </div>
        )}
        
        <div 
          className="pallet-grid"
          style={{ 
            '--box-cell-size': `${boxCellSize}px`,
            gridTemplateColumns: getGridTemplateColumns(),
            gridTemplateRows: `repeat(${alturaPallet}, var(--box-cell-size))`
          }}
        >
          {/* Separadores verticales entre caras */}
          {distribucionCaras.length > 1 && distribucionCaras.map((cols, index) => {
            if (index === 0) return null; // No hay separador antes de la primera cara
            
            // Calcular columna del separador
            const colAnterior = distribucionCaras.slice(0, index).reduce((sum, c) => sum + c, 0);
            const gridCol = colAnterior + index; // +index por los separadores anteriores
            
            return (
              <div
                key={`separator-${index}`}
                className="cara-separator"
                style={{
                  gridColumn: `${gridCol} / span 1`,
                  gridRow: '1 / -1',
                  alignSelf: 'stretch',
                  justifySelf: 'stretch'
                }}
              />
            );
          })}
          
          {palletData.cajas.map((caja) => {
            // Calcular row desde abajo (capa 1 en la parte inferior)
            const rowFromTop = caja.capa;
            const rowFromBottom = alturaPallet - rowFromTop + 1;
            const col = ((caja.numero_local - 1) % basePallet) + 1;
            
            // Calcular gridColumn considerando separadores
            const caraInfo = getCaraInfo(col);
            const gridCol = col + caraInfo.offsetCols;
            
            return (
              <div
                key={caja.numero}
                className={`box-cell ${caja.seleccionada ? 'box-selected' : ''}`}
                onClick={() => handleBoxClick(caja)}
                title={`Caja ${caja.numero} - Capa ${caja.capa}`}
                style={{
                  gridRow: rowFromBottom,
                  gridColumn: gridCol
                }}
              >
                <span className="box-number">{caja.numero}</span>
                {caja.seleccionada && (
                  <span className="box-indicator">✓</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Leyenda */}
      <div className="pallet-legend">
        <div className="legend-item">
          <div className="legend-box legend-box-normal"></div>
          <span>Normal</span>
        </div>
        <div className="legend-item">
          <div className="legend-box legend-box-muestra"></div>
          <span>Muestra</span>
        </div>
      </div>

      {/* Tooltip de información */}
      {selectedBox && (
        <div className="box-tooltip">
          <div className="tooltip-header">
            <h4>Información de Caja</h4>
            <button className="tooltip-close" onClick={handleCloseTooltip}>×</button>
          </div>
          <div className="tooltip-content">
            <div className="tooltip-row">
              <span className="tooltip-label">Número de Caja:</span>
              <span className="tooltip-value">{selectedBox.numero}</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">Capa:</span>
              <span className="tooltip-value">{selectedBox.capa}</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">Pallet:</span>
              <span className="tooltip-value">{palletData.numero_pallet}</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">Estado:</span>
              <span className={`tooltip-value ${selectedBox.seleccionada ? 'status-muestra' : 'status-normal'}`}>
                {selectedBox.seleccionada ? 'MUESTRA' : 'NORMAL'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DiagramaPallet;
