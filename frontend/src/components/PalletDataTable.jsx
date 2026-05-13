/**
 * PalletDataTable - Tabla editable para ingreso de datos de pallets
 * Permite editar certificados de pre-muestreo e inspección
 * Botones individuales para replicar correlativos desde una fila
 */

import { useState } from 'react';
import './PalletDataTable.css';

function PalletDataTable({ pallets = [], onDataChange, selectedType = 'NORMAL' }) {
  const [editedPallets, setEditedPallets] = useState(
    pallets.map(p => ({
      ...p,
      certificado_premuestreo: '',
      certificado_inspeccion: ''
    }))
  );

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const handleInputChange = (index, field, value) => {
    const updated = [...editedPallets];
    updated[index][field] = value;
    setEditedPallets(updated);
    
    // Notificar cambios al componente padre
    if (onDataChange) {
      onDataChange(updated);
    }
  };

  /**
   * Replica el certificado desde una fila hacia abajo
   * @param {number} startIndex - Índice de la fila donde comienza
   * @param {string} field - Campo a replicar (certificado_premuestreo o certificado_inspeccion)
   */
  const replicateCorrelativeFromRow = (startIndex, field) => {
    const updated = [...editedPallets];
    const startValue = updated[startIndex][field];
    
    if (!startValue) {
      alert('Por favor ingresa un valor en el certificado primero');
      return;
    }
    
    // Extraer número del certificado (últimos dígitos)
    const numberMatch = startValue.match(/(\d+)$/);
    if (!numberMatch) {
      alert('El certificado debe terminar con un número');
      return;
    }
    
    const startNumber = parseInt(numberMatch[1]);
    const prefix = startValue.substring(0, startValue.length - numberMatch[1].length);
    const digitCount = numberMatch[1].length;
    
    // Replicar desde la fila actual hacia abajo
    let number = startNumber;
    for (let i = startIndex; i < updated.length; i++) {
      updated[i][field] = `${prefix}${String(number).padStart(digitCount, '0')}`;
      number++;
    }
    
    setEditedPallets(updated);
    if (onDataChange) {
      onDataChange(updated);
    }
  };

  // Paginación
  const totalPages = Math.ceil(editedPallets.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const displayedPallets = editedPallets.slice(startIndex, endIndex);

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  if (!pallets || pallets.length === 0) {
    return (
      <div className="pallet-data-table">
        <div className="empty-state">
          <p>No hay pallets para mostrar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pallet-data-table">
      <div className="table-info">
        <h3>Datos de Pallets</h3>
        <p>Total de pallets: <strong>{editedPallets.length}</strong></p>
        <p style={{ fontSize: '0.85em', color: '#666' }}>
          💡 Ingresa el primer certificado y presiona el botón <strong>➜</strong> para replicar hacia abajo
        </p>
      </div>

      <div className="table-wrapper">
        <table className="pallets-table">
          <thead>
            <tr>
              <th className="col-folio">Folio Pallet</th>
              <th className="col-cajas">Cajas</th>
              <th className="col-certif-pre">Certificado de pre muestreo</th>
              <th className="col-certif-insp">Certificado de inspección</th>
            </tr>
          </thead>
          <tbody>
            {displayedPallets.map((pallet, displayIndex) => {
              const actualIndex = startIndex + displayIndex;
              return (
                <tr key={actualIndex} className="pallet-row">
                  <td className="col-folio">
                    <input
                      type="text"
                      value={pallet.folio_pallet}
                      disabled
                      className="input-disabled"
                    />
                  </td>
                  <td className="col-cajas">
                    <input
                      type="number"
                      value={pallet.cajas}
                      disabled
                      className="input-disabled"
                    />
                  </td>
                  {selectedType === 'NORMAL' && (
                    <>
                      <td className="col-certif-pre">
                        <div className="input-group-with-button">
                          <input
                            type="text"
                            placeholder="Ej: CERT-001"
                            value={pallet.certificado_premuestreo}
                            onChange={(e) =>
                              handleInputChange(actualIndex, 'certificado_premuestreo', e.target.value)
                            }
                            className="input-editable"
                          />
                          <button
                            onClick={() => replicateCorrelativeFromRow(actualIndex, 'certificado_premuestreo')}
                            className="btn-replicate"
                            title="Replicar certificado desde esta fila hacia abajo"
                            disabled={!pallet.certificado_premuestreo}
                          >
                            ➜
                          </button>
                        </div>
                      </td>
                      <td className="col-certif-insp">
                        <div className="input-group-with-button">
                          <input
                            type="text"
                            placeholder="Ej: CERT-001"
                            value={pallet.certificado_inspeccion}
                            onChange={(e) =>
                              handleInputChange(actualIndex, 'certificado_inspeccion', e.target.value)
                            }
                            className="input-editable"
                          />
                          <button
                            onClick={() => replicateCorrelativeFromRow(actualIndex, 'certificado_inspeccion')}
                            className="btn-replicate"
                            title="Replicar certificado desde esta fila hacia abajo"
                            disabled={!pallet.certificado_inspeccion}
                          >
                            ➜
                          </button>
                        </div>
                      </td>
                    </>
                  )}
                  {selectedType === 'ETAPA' && (
                    <>
                      <td className="col-etapa-pre">
                        <div className="input-group-with-button">
                          <input
                            type="text"
                            placeholder="Verificado"
                            value={pallet.certificado_premuestreo}
                            onChange={(e) =>
                              handleInputChange(actualIndex, 'certificado_premuestreo', e.target.value)
                            }
                            className="input-editable"
                          />
                          <button
                            onClick={() => replicateCorrelativeFromRow(actualIndex, 'certificado_premuestreo')}
                            className="btn-replicate"
                            title="Replicar desde esta fila hacia abajo"
                            disabled={!pallet.certificado_premuestreo}
                          >
                            ➜
                          </button>
                        </div>
                      </td>
                      <td className="col-etapa-insp">
                        <div className="input-group-with-button">
                          <input
                            type="text"
                            placeholder="Verificado"
                            value={pallet.certificado_inspeccion}
                            onChange={(e) =>
                              handleInputChange(actualIndex, 'certificado_inspeccion', e.target.value)
                            }
                            className="input-editable"
                          />
                          <button
                            onClick={() => replicateCorrelativeFromRow(actualIndex, 'certificado_inspeccion')}
                            className="btn-replicate"
                            title="Replicar desde esta fila hacia abajo"
                            disabled={!pallet.certificado_inspeccion}
                          >
                            ➜
                          </button>
                        </div>
                      </td>
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <button 
          onClick={handlePrevPage} 
          disabled={currentPage === 1}
          className="btn-pagination"
        >
          ← Anterior
        </button>
        
        <div className="page-info">
          Página {currentPage} de {totalPages}
        </div>
        
        <button 
          onClick={handleNextPage} 
          disabled={currentPage === totalPages}
          className="btn-pagination"
        >
          Siguiente →
        </button>
      </div>

      <div className="table-summary">
        <div className="summary-item">
          <span>Total de cajas:</span>
          <strong>{editedPallets.reduce((sum, p) => sum + (p.cajas || 0), 0)}</strong>
        </div>
        <div className="summary-item">
          <span>Pre-muestreos completados:</span>
          <strong>{editedPallets.filter(p => p.certificado_premuestreo).length} / {editedPallets.length}</strong>
        </div>
        <div className="summary-item">
          <span>Inspecciones completadas:</span>
          <strong>{editedPallets.filter(p => p.certificado_inspeccion).length} / {editedPallets.length}</strong>
        </div>
      </div>

      {/* Export data for parent */}
      <div className="export-data" style={{ display: 'none' }} data-pallets={JSON.stringify(editedPallets)}></div>
    </div>
  );
}

export default PalletDataTable;
