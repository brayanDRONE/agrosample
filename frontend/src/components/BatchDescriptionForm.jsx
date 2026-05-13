/**
 * BatchDescriptionForm - Formulario para carga y procesamiento de archivos .INS
 */

import { useEffect, useState, useRef } from 'react';
import batchDescriptionService from '../services/batchDescriptionService';
import PalletDataTable from './PalletDataTable';
import FolioOrderPanel from './FolioOrderPanel';
import './BatchDescriptionForm.css';

function BatchDescriptionForm({
  currentStep,
  fileData,
  selectedType,
  onFileLoaded,
  onTypeSelected,
  onFolioOrderConfirmed,
  onGoToTypeSelect,
  onNewBatch
}) {
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [editedPallets, setEditedPallets] = useState(null);
  const [editableData, setEditableData] = useState({
    especie: '',
    tipo_seleccion: 'X',
    tipo_despacho: 'X'
  });

  useEffect(() => {
    if (currentStep === 'data-entry' && fileData?.header) {
      setEditableData((current) => ({
        especie: current.especie || fileData.header.especie || '',
        tipo_seleccion: current.tipo_seleccion || 'X',
        tipo_despacho: current.tipo_despacho || 'X'
      }));
    }
  }, [currentStep, fileData]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.INS') || file.name.endsWith('.ins')) {
        handleFileUpload(file);
      } else {
        setError('Por favor seleccione un archivo .INS válido');
      }
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    setLoading(true);
    setError(null);

    try {
      const response = await batchDescriptionService.parseInsFile(file);

      if (response.success) {
        onFileLoaded(response.data);
      } else {
        setError(response.message || 'Error al procesar el archivo');
      }
    } catch (err) {
      console.error('Error uploading file:', err);
      setError(
        err.message ||
        'Error al procesar el archivo. Verifique que sea un archivo .INS válido'
      );
    } finally {
      setLoading(false);
    }
  };

  // STEP 1: Upload
  if (currentStep === 'upload') {
    return (
      <div className="batch-description-container">
        <div className="upload-step">
          <div className="step-header">
            <h1>Generar Planilla de Descripción de Lote</h1>
            <p>Paso 1: Cargar archivo .INS</p>
          </div>

          <div
            className={`drop-zone ${dragActive ? 'active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex="0"
            onKeyPress={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".INS,.ins"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
              disabled={loading}
            />
            
            <div className="drop-zone-content">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 2v20M2 12h20M12 2l-7 7M12 2l7 7" />
              </svg>
              <h3>Arrastre el archivo aquí</h3>
              <p>o haga clic para seleccionar</p>
              <p className="file-info">Formato: .INS (Anexo N° 5 USDA)</p>
            </div>

            {loading && (
              <div className="loading-overlay">
                <div className="spinner"></div>
                <p>Procesando archivo...</p>
              </div>
            )}
          </div>

          {error && (
            <div className="error-box">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          <div className="info-box">
            <h4>Información del archivo</h4>
            <ul>
              <li>Formato: Archivo plano (.INS) con estructura de 35 caracteres de encabezado</li>
              <li>Contenido: SIF + Planta + Especie + País1 + País2 + Fecha + Total de Pallets</li>
              <li>Registros: Folio Pallet + Cantidad de Cajas por registro</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // STEP 2: Type Select
  if (currentStep === 'type-select' && fileData) {
    return (
      <div className="batch-description-container">
        <div className="type-select-step">
          <div className="step-header">
            <h1>Seleccionar Tipo de Muestreo</h1>
            <p>Paso 2: Elija el tipo de inspección para esta planilla</p>
          </div>

          <div className="type-options">
            <div
              className="type-option normal-type"
              onClick={() => onTypeSelected('NORMAL')}
              role="button"
              tabIndex="0"
              onKeyPress={(e) => e.key === 'Enter' && onTypeSelected('NORMAL')}
            >
              <div className="type-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 10h18M3 6h18M3 14h18M3 18h18" />
                </svg>
              </div>
              <h3>NORMAL</h3>
              <p>Muestreo con tabla de datos estructurada</p>
            </div>

            <div
              className="type-option etapa-type"
              onClick={() => onTypeSelected('ETAPA')}
              role="button"
              tabIndex="0"
              onKeyPress={(e) => e.key === 'Enter' && onTypeSelected('ETAPA')}
            >
              <div className="type-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 3h4v4H5V3zm6 0h4v4h-4V3zm6 0h4v4h-4V3zM5 9h4v4H5V9zm6 0h4v4h-4V9zm6 0h4v4h-4V9zM5 15h4v4H5v-4zm6 0h4v4h-4v-4zm6 0h4v4h-4v-4z" />
                </svg>
              </div>
              <h3>POR ETAPA</h3>
              <p>Muestreo por etapas con vista de cámara</p>
            </div>
          </div>

          <button className="btn-back" onClick={onNewBatch}>
            Cargar otro archivo
          </button>
        </div>
      </div>
    );
  }

  // STEP 2.5: Folio Order (solo para ETAPA)
  if (currentStep === 'folio-order' && fileData) {
    return (
      <div className="batch-description-container">
        <div className="folio-order-step">
          <div className="step-header" style={{ marginBottom: '24px' }}>
            <p style={{ margin: 0, color: '#6b7280', fontSize: '0.9rem' }}>
              Paso 2 (ETAPA): Ordenar folios según posición en cámara de frío
            </p>
          </div>
          <FolioOrderPanel
            pallets={fileData.pallets}
            onConfirm={onFolioOrderConfirmed}
            onBack={onGoToTypeSelect || onNewBatch}
          />
          <div style={{ marginTop: '16px' }}>
            <button
              className="btn-back"
              onClick={onNewBatch}
              style={{ fontSize: '0.85rem', opacity: 0.7 }}
            >
              ← Volver al inicio
            </button>
          </div>
        </div>
      </div>
    );
  }

  // STEP 3: Data Entry
  if (currentStep === 'data-entry' && fileData && selectedType) {
    const handleSaveData = async () => {
      if (!editedPallets || editedPallets.length === 0) {
        setError('No hay datos de pallets para guardar');
        return;
      }

      // Validar que todos los certificados estén completos
      const incompleteRows = editedPallets.filter(
        p => !p.certificado_premuestreo || !p.certificado_inspeccion
      );

      if (incompleteRows.length > 0) {
        setError(
          `${incompleteRows.length} fila(s) sin completar. Por favor complete todos los certificados.`
        );
        return;
      }

      setLoading(true);
      setError(null);

      try {
        console.log('[SAVE] Iniciando guardado de planilla...');
        console.log('[SAVE] Datos a enviar:', {
          header: fileData.header,
          type: selectedType,
          pallet_count: editedPallets.length,
          especie: editableData.especie,
          tipo_seleccion: editableData.tipo_seleccion,
          tipo_despacho: editableData.tipo_despacho
        });

        // Enviar datos al backend para generar PDF
        const response = await batchDescriptionService.saveBatchDescription({
          header: fileData.header,
          pallets: editedPallets,
          type: selectedType,
          especie: editableData.especie,
          tipo_seleccion: editableData.tipo_seleccion,
          tipo_despacho: editableData.tipo_despacho
        });

        console.log('[SAVE] Respuesta del servidor:', response);

        if (response.success && response.pdf_url) {
          // Descargar PDF
          console.log('[SAVE] Descargando PDF desde:', response.pdf_url);
          
          try {
            // Descargar el PDF como blob
            const pdfResponse = await fetch(response.pdf_url);
            if (!pdfResponse.ok) {
              throw new Error(`Error al descargar PDF: ${pdfResponse.status}`);
            }
            
            const pdfBlob = await pdfResponse.blob();
            console.log('[SAVE] PDF descargado, tamaño:', pdfBlob.size, 'bytes');
            
            if (pdfBlob.size === 0) {
              setError('El PDF generado está vacío. Por favor intenta nuevamente.');
              setLoading(false);
              return;
            }
            
            // Crear URL local para el blob
            const blobUrl = URL.createObjectURL(pdfBlob);
            
            // Crear link y simular descarga
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = response.filename || 'planilla.pdf';
            document.body.appendChild(link);
            link.click();
            
            // Limpiar
            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);
            
            console.log('[SAVE] PDF descargado exitosamente');
            
            // Mostrar mensaje de éxito
            alert('Planilla generada y descargada exitosamente');
            // Volver al inicio
            onNewBatch();
          } catch (downloadErr) {
            console.error('[SAVE] Error descargando PDF:', downloadErr);
            setError(`Error descargando PDF: ${downloadErr.message}`);
          }
        } else {
          setError(response.message || 'Error al generar la planilla');
        }
      } catch (err) {
        console.error('[SAVE] Error:', err);
        const errorMsg = err.errors?.[0] || err.message || 'Error al guardar los datos';
        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    return (
      <div className="batch-description-container">
        <div className="data-entry-step">
          <div className="step-header">
            <h1>Ingreso de Certificados - {selectedType}</h1>
            <p>Paso 3: Complete los números de certificados para cada pallet</p>
          </div>

          <div className="data-entry-content">
            <div className="info-header">
              <div className="info-item">
                <span className="label">Tipo de Muestreo:</span>
                <span className="value">{selectedType}</span>
              </div>
              <div className="info-item">
                <span className="label">Total de Pallets:</span>
                <span className="value">{fileData.total_pallets}</span>
              </div>
              {fileData.header && (
                <>
                  <div className="info-item">
                    <span className="label">SIF:</span>
                    <span className="value">{fileData.header.sif}</span>
                  </div>
                  <div className="info-item">
                    <span className="label">Fecha:</span>
                    <span className="value">{fileData.header.fecha}</span>
                  </div>
                </>
              )}
            </div>

            {/* Campos editables para info faltante */}
            <div className="editable-fields-section">
              <h3>Información del Lote</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="especie">ESPECIE *</label>
                  <input
                    id="especie"
                    type="text"
                    placeholder="Ingrese la especie"
                    value={editableData.especie}
                    onChange={(e) => setEditableData({ ...editableData, especie: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="tipo_seleccion">Tipo de Selección</label>
                  <input
                    id="tipo_seleccion"
                    type="text"
                    placeholder="Ingrese el código de selección"
                    value={editableData.tipo_seleccion}
                    onChange={(e) => setEditableData({ ...editableData, tipo_seleccion: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="tipo_despacho">Tipo de Despacho</label>
                  <input
                    id="tipo_despacho"
                    type="text"
                    placeholder="Ingrese el código de despacho"
                    value={editableData.tipo_despacho}
                    onChange={(e) => setEditableData({ ...editableData, tipo_despacho: e.target.value })}
                    className="input-field"
                  />
                </div>
              </div>
            </div>

            <div className="section-divider" />

            {error && (
              <div className="error-box">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            <div className="pallet-table-section">
              <PalletDataTable 
                pallets={fileData.pallets} 
                selectedType={selectedType}
                onDataChange={(data) => {
                  setEditedPallets(data);
                }}
              />
            </div>

            <div className="navigation-buttons">
              <button 
                className="btn-back" 
                onClick={() => onNewBatch()}
                disabled={loading}
              >
                ← Volver al inicio
              </button>
              <button 
                className="btn-save" 
                onClick={handleSaveData}
                disabled={loading}
              >
                {loading ? 'Generando...' : 'Guardar y Generar PDF ✓'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default BatchDescriptionForm;
