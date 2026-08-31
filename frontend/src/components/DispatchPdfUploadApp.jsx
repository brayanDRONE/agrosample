import React, { useState } from 'react';
import { ThemeProvider, useTheme } from '../contexts/ThemeContext';
import Header from './Header';
import './DispatchPdfUploadApp.css';

function DispatchPdfUploadAppContent() {
  const { theme } = useTheme();
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setMessage('');
    } else {
      setMessage('Por favor, selecciona un archivo PDF válido.');
      setMessageType('error');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
      setMessage('');
    } else {
      setMessage('Por favor, selecciona un archivo PDF válido.');
      setMessageType('error');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Por favor, selecciona un archivo PDF.');
      setMessageType('error');
      return;
    }

    const formData = new FormData();
    formData.append('pdf_file', file);

    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('/api/dispatch-flatfile/generate-from-pdf/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        // Intentar leer el mensaje de error real del cuerpo JSON
        let errorMessage = `Error del servidor (${response.status})`;
        try {
          const errorData = await response.json();
          if (errorData.message) {
            errorMessage = errorData.message;
          } else if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (_) {
          // Si no es JSON, usar el mensaje genérico
        }
        throw new Error(errorMessage);
      }

      // Get planilla data from headers if available
      const planillaDataStr = response.headers.get('X-Planilla-Data');
      let extractedDataFromHeader = null;
      if (planillaDataStr) {
        try {
          extractedDataFromHeader = JSON.parse(planillaDataStr);
          setExtractedData(extractedDataFromHeader);
        } catch (e) {
          console.warn('Could not parse planilla data from header');
        }
      }

      // Get the file from response
      const blob = await response.blob();
      const filename = response.headers.get('X-File-Name') || 'multipuerto.txt';

      // Download the file
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.parentElement.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      setMessage('Planilla procesada exitosamente. El archivo se ha descargado.');
      setMessageType('success');
    } catch (error) {
      console.error('Error:', error);
      setMessage(`Error: ${error.message}`);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setExtractedData(null);
    setMessage('');
  };

  return (
    <div className="app">
      <Header />
      
      <main className="main-container">
        <div className="content-wrapper">
          <div className="form-section-container">
            <div className="form-section-header">
              <h1>Generar Archivo Plano de Despacho</h1>
              <p className="form-subtitle">Paso 1: Cargar archivo PDF</p>
            </div>

            {message && (
              <div className={`message ${messageType}`}>
                <span>{messageType === 'error' ? '❌' : '✅'}</span>
                <span>{message}</span>
              </div>
            )}

            <div className="upload-zone-wrapper">
              <label
                className="file-input-label"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                <span className="upload-icon">📄</span>
                <span className="upload-text">
                  Arrastra tu PDF aquí o haz clic para seleccionar
                </span>
                <input
                  type="file"
                  accept=".pdf"
                  className="file-input"
                  onChange={handleFileChange}
                />
              </label>

              <div style={{ marginTop: '16px' }}>
                {file && (
                  <p style={{ fontSize: '13px', color: '#666', marginBottom: '12px' }}>
                    ✓ Archivo seleccionado: {file.name}
                  </p>
                )}
              </div>
            </div>

            <div className="button-group">
              <button
                className={`btn btn-primary ${loading ? 'loading' : ''}`}
                onClick={handleUpload}
                disabled={!file || loading}
              >
                {loading ? 'Procesando...' : 'Procesar Planilla'}
              </button>
              {(file || extractedData) && (
                <button
                  className="btn btn-secondary"
                  onClick={handleClear}
                  disabled={loading}
                >
                  Limpiar
                </button>
              )}
            </div>

            {/* Información del archivo */}
            <div className="file-info-section">
              <h3>Información del archivo</h3>
              <ul className="file-info-list">
                <li>Formato: PDF de Planilla SAG</li>
                <li>Contenido: Folio SAG + Exportador + Especie + Cantidad + Contenedor + Datos de Despacho</li>
                <li>Salida: Archivo .txt en formato Multipuerto de 42 campos delimitados por punto y coma</li>
              </ul>
            </div>

            {/* Datos Extraídos */}
            {extractedData && (
              <div className="extracted-data-section">
                <h3>Datos Extraídos de la Planilla</h3>
                <div className="data-grid">
                  {[
                    { key: 'folio_sag', label: 'Folio SAG' },
                    { key: 'nro_planilla', label: 'Nro Planilla' },
                    { key: 'exportador', label: 'Exportador' },
                    { key: 'especie', label: 'Especie' },
                    { key: 'variedad', label: 'Variedad' },
                    { key: 'cantidad_kg', label: 'Cantidad KG' },
                    { key: 'puerto_destino', label: 'Puerto Destino' },
                    { key: 'pais_destino', label: 'País Destino' },
                    { key: 'contenedor', label: 'Contenedor' },
                    { key: 'fecha_despacho', label: 'Fecha Despacho' },
                    { key: 'establecimiento', label: 'Establecimiento' },
                    { key: 'nombre_despachador', label: 'Despachador' },
                  ].map(({ key, label }) => (
                    <div key={key} className="data-item">
                      <div className="data-key">{label}</div>
                      <div className="data-value">
                        {extractedData[key] || '-'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default function DispatchPdfUploadApp() {
  return (
    <ThemeProvider>
      <DispatchPdfUploadAppContent />
    </ThemeProvider>
  );
}
