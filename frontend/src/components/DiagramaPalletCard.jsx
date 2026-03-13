/**
 * DiagramaPalletCard - Tarjeta estilo INACAP para visualizar pallets
 * 
 * Muestra un pallet con estructura de tarjeta moderna con:
 * - Header con background y código del pallet
 * - Información del pallet
 * - Indicador de porcentaje de muestras
 * - Menú de opciones
 */

import { useState } from 'react';
import './DiagramaPalletCard.css';

function DiagramaPalletCard({ palletData, onExpand, onDelete, onEdit }) {
  const [showMenu, setShowMenu] = useState(false);

  // Calcular porcentaje de muestras
  const totalCajas = palletData.fin_caja - palletData.inicio_caja + 1;
  const porcentajeCompletado = totalCajas > 0 
    ? Math.round((palletData.total_cajas_muestra / totalCajas) * 100)
    : 0;

  // Colores de fondo gradiente (rotativo)
  const colores = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
  ];
  
  const colorIndex = (palletData.numero_pallet % colores.length);
  const backgroundColor = colores[colorIndex];

  const handleMenuClick = (action) => {
    setShowMenu(false);
    if (action === 'expand') onExpand && onExpand(palletData);
    if (action === 'edit') onEdit && onEdit(palletData);
    if (action === 'delete') onDelete && onDelete(palletData);
  };

  return (
    <div className="pallet-card-container">
      {/* Header con background y código */}
      <div className="pallet-card-header" style={{ background: backgroundColor }}>
        <div className="pallet-card-code">
          P{String(palletData.numero_pallet).padStart(3, '0')}
        </div>
      </div>

      {/* Cuerpo de la tarjeta */}
      <div className="pallet-card-body">
        {/* Título */}
        <h3 className="pallet-card-title">
          Pallet {palletData.numero_pallet}
        </h3>

        {/* Información del pallet */}
        <div className="pallet-card-info">
          <div className="info-item">
            <span className="info-label">Cajas:</span>
            <span className="info-value">
              {palletData.inicio_caja} - {palletData.fin_caja}
            </span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Total:</span>
            <span className="info-value">{totalCajas} cajas</span>
          </div>

          <div className="info-item">
            <span className="info-label">Muestras:</span>
            <span className={`info-value ${palletData.total_cajas_muestra > 0 ? 'muestra-badge' : ''}`}>
              {palletData.total_cajas_muestra}
            </span>
          </div>
        </div>

        {/* Porcentaje de completado */}
        <div className="pallet-card-progress">
          <div className="progress-label">
            <span>{porcentajeCompletado}% completado</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${porcentajeCompletado}%` }}
            ></div>
          </div>
        </div>

        {/* Línea divisora */}
        <div className="pallet-card-divider"></div>

        {/* Footer con acciones */}
        <div className="pallet-card-footer">
          <button 
            className="pallet-card-expand"
            onClick={() => handleMenuClick('expand')}
            title="Ver detalles"
          >
            Ver detalles
          </button>

          {/* Menú de opciones */}
          <div className="pallet-card-menu">
            <button 
              className="menu-button"
              onClick={() => setShowMenu(!showMenu)}
              title="Más opciones"
            >
              ⋮
            </button>
            
            {showMenu && (
              <div className="menu-dropdown">
                <button 
                  onClick={() => handleMenuClick('edit')}
                  className="menu-item edit"
                >
                  ✎ Editar
                </button>
                <button 
                  onClick={() => handleMenuClick('delete')}
                  className="menu-item delete"
                >
                  ⊗ Eliminar
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DiagramaPalletCard;
