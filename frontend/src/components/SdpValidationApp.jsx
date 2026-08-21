/**
 * SdpValidationApp - Punto de entrada para el módulo de validación de SDP
 */

import { useRef, useState } from 'react';
import { ThemeProvider } from '../contexts/ThemeContext';
import Header from './Header';
import { validateSdpExcel } from '../services/sdpValidationService';
import './SdpValidationApp.css';

function SdpValidationAppContent() {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] || null;
    setFile(selectedFile);
    setReport(null);
    setError(null);
    event.target.value = '';
  };

  const handleNewValidation = () => {
    setFile(null);
    setReport(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setError('Seleccione un archivo Excel para comenzar');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setReport(await validateSdpExcel(file));
    } catch (requestError) {
      setError(requestError.message || 'No se pudo procesar el archivo Excel');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <Header />
      <main className="main-container">
        <div className="content-wrapper">
          <div className="sdp-validation-container">
            <div className="sdp-validation-header">
              <span className="sdp-kicker">SAG-USA</span>
              <h1>Validación de SDP</h1>
              <p>Cargue el Excel para cruzar sus registros con los sitios de producción aprobados.</p>
            </div>

            <form className="sdp-upload-panel" onSubmit={handleSubmit}>
              <label htmlFor="sdp-excel-file">Archivo Excel</label>
              <div className="sdp-upload-row">
                <input
                  ref={fileInputRef}
                  id="sdp-excel-file"
                  className="sdp-file-input"
                  type="file"
                  accept=".xlsx,.xlsm"
                  onChange={handleFileChange}
                />
                <label className="sdp-file-picker" htmlFor="sdp-excel-file">
                  <span className="sdp-file-picker-icon">↑</span>
                  <span>Seleccionar Excel</span>
                </label>
                <button type="submit" disabled={loading || !file}>
                  {loading ? 'Validando...' : 'Validar SDP'}
                </button>
              </div>
              <span className="sdp-file-name">{file ? file.name : 'Formatos aceptados: .xlsx y .xlsm'}</span>
            </form>

            {error && <div className="sdp-error" role="alert">{error}</div>}

            {report && (
              <section className="sdp-report" aria-live="polite">
                <div className="sdp-report-heading">
                  <div>
                    <span className="sdp-kicker">Resultado consolidado</span>
                    <h2>Resumen de validación</h2>
                  </div>
                  <div className="sdp-report-actions">
                    <button type="button" className="sdp-new-validation" onClick={handleNewValidation}>
                      Nueva validación
                    </button>
                    <a className="sdp-download" href={report.pdf_url} target="_blank" rel="noreferrer" download>
                      Descargar PDF
                    </a>
                  </div>
                </div>
                <div className="sdp-summary-grid">
                  <div><strong>{report.summary.total}</strong><span>Registros</span></div>
                  <div className="is-valid"><strong>{report.summary.cumplen}</strong><span>Cumplen</span></div>
                  <div className="is-invalid"><strong>{report.summary.no_cumplen}</strong><span>No cumplen</span></div>
                  <div><strong>{report.summary.consultas_unicas}</strong><span>Consultas únicas</span></div>
                </div>
                <div className="sdp-table-wrap">
                  <table>
                    <thead>
                      <tr><th>CSG</th><th>SDP</th><th>Provincia Excel</th><th>Comuna Excel</th><th>Variedad Comercial</th><th>Productor</th><th>Estado</th><th>Observaciones</th></tr>
                    </thead>
                    <tbody>
                      {report.results.map((result) => (
                        <tr key={result.sdp}>
                          <td>{result.csg}</td>
                          <td>{result.sdp}</td>
                          <td>{result.provincia}</td>
                          <td>{result.comuna}</td>
                          <td>{result.variedad_comercial}</td>
                          <td>{result.datos_sag?.productor || '-'}</td>
                          <td><span className={`sdp-status ${result.cumple ? 'valid' : 'invalid'}`}>{result.cumple ? 'CUMPLE' : 'NO CUMPLE'}</span></td>
                          <td>{result.diferencias.join('; ') || 'Sin diferencias'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function SdpValidationApp() {
  return (
    <ThemeProvider>
      <SdpValidationAppContent />
    </ThemeProvider>
  );
}

export default SdpValidationApp;