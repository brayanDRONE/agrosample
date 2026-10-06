import { useEffect, useState } from 'react';
import { ThemeProvider } from '../contexts/ThemeContext';
import Header from './Header';
import { downloadCherryChinaPdf, getCherryChinaQuota, getCherryChinaReportStatus, validateCherryChina } from '../services/cherryChinaValidationService';
import './CherryChinaValidationApp.css';

function displayStatus(value) {
  if (value === true || value === 'SI' || value === 'Sí') return 'Sí';
  if (value === false || value === 'NO' || value === 'No') return 'No';
  return 'No verificado';
}

function CheckRow({ label, value }) {
  const status = displayStatus(value);
  const statusClass = status === 'Sí' ? 'is-valid' : status === 'No' ? 'is-invalid' : 'is-unknown';
  return (
    <div className="china-check-row">
      <span>{label}</span>
      <strong className={statusClass}>{status}</strong>
    </div>
  );
}

function MiniIconButton({ label, icon, onClick, disabled }) {
  return (
    <button
      className="china-icon-button"
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
    >
      {icon === 'edit' ? (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 16.5V20h3.5L19 8.5 15.5 5 4 16.5Z" />
          <path d="m13.8 6.7 3.5 3.5" />
        </svg>
      ) : icon === 'delete' ? (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 7h16M9 7V4h6v3m3 0-1 13H7L6 7m4 4v5m4-5v5" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m5 12 4 4L19 6" />
        </svg>
      )}
    </button>
  );
}

function ResultCard({ title, result }) {
  if (!result?.code) return null;
  return (
    <section className="china-result-card">
      <h3>{title} {result.code ? `· ${result.code}` : ''}</h3>
      <div className="china-check-list">
        {result.active !== undefined && <CheckRow label="Activo en SRA" value={result.active} />}
        {result.china_registered !== undefined && <CheckRow label="Inscrito para China" value={result.china_registered} />}
        {result.china_cherry_approved !== undefined && <CheckRow label="ChinaPort · habilitado para cereza" value={result.china_cherry_approved} />}
        {result.china_approved !== undefined && <CheckRow label="Aprobado para China" value={result.china_approved} />}
        {result.mosca_campaign_found !== undefined && <CheckRow label="Figura en listado de campañas de mosca" value={result.mosca_campaign_found} />}
        {result.mosca_campaign_current !== undefined && <CheckRow label="Campaña vigente" value={result.mosca_campaign_current} />}
        {result.descolgado_china !== undefined && <CheckRow label="Descolgado para China (cereza)" value={result.descolgado_china} />}
      </div>
      {result.producer_name && <p><strong>Productor:</strong> {result.producer_name}</p>}
      {result.chinaport_product_name && <p><strong>Producto ChinaPort:</strong> {result.chinaport_product_name} ({result.chinaport_scientific_name || '-'})</p>}
      {result.species && <p><strong>Especie:</strong> {result.species.join(', ')}</p>}
      {result.varieties?.length > 0 && <p><strong>Variedades:</strong> {result.varieties.join(', ')}</p>}
      {result.mosca_campaigns?.length > 0 && (
        <div className="china-detail-list">
          <strong>Campañas y países vigentes</strong>
          {result.mosca_campaigns.map((item, index) => (
            <div key={`${item.campaign}-${item.country}-${index}`}>
              {item.campaign} · {item.country}
            </div>
          ))}
        </div>
      )}
      {result.descolgados?.length > 0 && (
        <div className="china-detail-list">
          <strong>Detecciones relevantes para China</strong>
          {result.descolgados.map((item, index) => (
            <div key={`${item.variety}-${item.pest}-${index}`}>
              {item.variety} · {item.pest} · {item.target_country}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function CherryChinaValidationContent() {
  const [csgs, setCsgs] = useState([]);
  const [csgDraft, setCsgDraft] = useState('');
  const [editingCsgIndex, setEditingCsgIndex] = useState(null);
  const [editingCsgDraft, setEditingCsgDraft] = useState('');
  const [csps, setCsps] = useState([]);
  const [cspDraft, setCspDraft] = useState('');
  const [editingCspIndex, setEditingCspIndex] = useState(null);
  const [editingCspDraft, setEditingCspDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const [report, setReport] = useState(null);
  const [quota, setQuota] = useState(null);

  useEffect(() => {
    let active = true;
    getCherryChinaQuota()
      .then((accountQuota) => {
        if (active) setQuota(accountQuota);
      })
      .catch(() => {});
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const reportId = report?.report_id;
    if (!reportId || !['QUEUED', 'PROCESSING'].includes(report.status)) return undefined;

    let stopped = false;
    let timer;
    const poll = async () => {
      try {
        const current = await getCherryChinaReportStatus(reportId);
        if (stopped) return;
        setReport(current);
        if (current.quota) setQuota(current.quota);
        if (current.status === 'FAILED') {
          setError(current.message || 'No se pudo generar el informe.');
        } else if (['QUEUED', 'PROCESSING'].includes(current.status)) {
          timer = window.setTimeout(poll, 2000);
        }
      } catch (pollError) {
        if (!stopped) {
          setError(pollError.message || 'No se pudo consultar el estado del informe.');
          timer = window.setTimeout(poll, 5000);
        }
      }
    };

    timer = window.setTimeout(poll, 1200);
    return () => {
      stopped = true;
      window.clearTimeout(timer);
    };
  }, [report?.report_id, report?.status]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const csgCodes = csgs.map((code) => code.trim()).filter(Boolean);
    const cspCodes = csps.map((code) => code.trim()).filter(Boolean);
    if (!csgCodes.length && !cspCodes.length) {
      setError('Ingrese un código CSG o CSP para iniciar la consulta.');
      return;
    }
    setLoading(true);
    setError('');
    setReport(null);
    try {
      const result = await validateCherryChina(csgCodes, cspCodes);
      setReport(result);
      if (result.quota) setQuota(result.quota);
    } catch (requestError) {
      if (requestError.quota) setQuota(requestError.quota);
      setError(requestError.message || 'No se pudo completar la consulta.');
    } finally {
      setLoading(false);
    }
  };

  const addCsg = () => {
    const code = csgDraft.trim();
    if (!/^\d{3,12}$/.test(code)) {
      setError('Ingrese un CSG de 3 a 12 dígitos.');
      return;
    }
    if (csgs.includes(code)) {
      setError('Ese CSG ya está en la lista.');
      return;
    }
    setCsgs((current) => [...current, code]);
    setCsgDraft('');
    setError('');
  };

  const saveCsgEdit = (index) => {
    const code = editingCsgDraft.trim();
    if (!/^\d{3,12}$/.test(code)) {
      setError('Ingrese un CSG de 3 a 12 dígitos.');
      return;
    }
    if (csgs.some((existing, itemIndex) => existing === code && itemIndex !== index)) {
      setError('Ese CSG ya está en la lista.');
      return;
    }
    setCsgs((current) => current.map((value, itemIndex) => itemIndex === index ? code : value));
    setEditingCsgIndex(null);
    setEditingCsgDraft('');
    setError('');
  };

  const addCsp = () => {
    const code = cspDraft.trim();
    if (!/^\d{3,12}$/.test(code)) {
      setError('Ingrese un CSP de 3 a 12 dígitos.');
      return;
    }
    if (csps.includes(code)) {
      setError('Ese CSP ya está en la lista.');
      return;
    }
    setCsps((current) => [...current, code]);
    setCspDraft('');
    setError('');
  };

  const saveCspEdit = (index) => {
    const code = editingCspDraft.trim();
    if (!/^\d{3,12}$/.test(code)) {
      setError('Ingrese un CSP de 3 a 12 dígitos.');
      return;
    }
    if (csps.some((existing, itemIndex) => existing === code && itemIndex !== index)) {
      setError('Ese CSP ya está en la lista.');
      return;
    }
    setCsps((current) => current.map((value, itemIndex) => itemIndex === index ? code : value));
    setEditingCspIndex(null);
    setEditingCspDraft('');
    setError('');
  };

  const handleDownload = async () => {
    setDownloading(true);
    setError('');
    try {
      await downloadCherryChinaPdf(report.report_id);
    } catch (downloadError) {
      setError(downloadError.message || 'No se pudo descargar el PDF.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="app">
      <Header />
      <main className="main-container">
        <div className="content-wrapper">
          <div className="china-validation-container">
            <header className="china-validation-header">
              <span className="china-kicker">AGROSAMPLE · SAG</span>
              <h1>Validación de cereza para China</h1>
              <p>Agregue los CSG y el CSP que desea revisar, sin cargar packing list.</p>
            </header>

            {quota && (
              <p className="china-quota" aria-live="polite">
                {quota.unlimited
                  ? 'Acceso ilimitado · consultas sin límite mensual'
                  : `${quota.plan === 'CUSTOM' ? 'Cupo asignado' : 'Plan gratuito'} · ${quota.remaining} de ${quota.limit} informes disponibles este mes`}
              </p>
            )}

            <form className="china-query-form" onSubmit={handleSubmit}>
              <div className="china-code-panels">
                <section className="china-code-panel" aria-labelledby="china-csg-heading">
                  <header>
                    <h2 id="china-csg-heading">CSG a consultar</h2>
                    <span>{csgs.length}</span>
                  </header>
                  <div className="china-code-add-row">
                    <input
                      aria-label="Nuevo código CSG"
                      placeholder="Ingrese código CSG"
                      value={csgDraft}
                      onChange={(event) => setCsgDraft(event.target.value)}
                      inputMode="numeric"
                      onKeyDown={(event) => event.key === 'Enter' && (event.preventDefault(), addCsg())}
                    />
                    <button type="button" className="china-add-button" onClick={addCsg} disabled={loading}>Agregar</button>
                  </div>
                  {csgs.length ? (
                    <ul className="china-code-list">
                      {csgs.map((code, index) => (
                        <li className="china-code-item" key={`${code}-${index}`}>
                          {editingCsgIndex === index ? (
                            <input
                              aria-label={`Editar CSG ${index + 1}`}
                              value={editingCsgDraft}
                              onChange={(event) => setEditingCsgDraft(event.target.value)}
                              inputMode="numeric"
                              autoFocus
                            />
                          ) : <strong>{code}</strong>}
                          <div className="china-code-actions">
                            {editingCsgIndex === index ? (
                              <>
                                <MiniIconButton label={`Guardar CSG ${index + 1}`} icon="save" onClick={() => saveCsgEdit(index)} />
                                <MiniIconButton label="Cancelar edición" icon="cancel" onClick={() => { setEditingCsgIndex(null); setEditingCsgDraft(''); setError(''); }} />
                              </>
                            ) : (
                              <>
                                <MiniIconButton label={`Editar CSG ${code}`} icon="edit" onClick={() => { setEditingCsgIndex(index); setEditingCsgDraft(code); setError(''); }} />
                                <MiniIconButton label={`Eliminar CSG ${code}`} icon="delete" onClick={() => setCsgs((current) => current.filter((_, itemIndex) => itemIndex !== index))} />
                              </>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : <p className="china-empty-list">Aún no hay CSG agregados.</p>}
                </section>

                <section className="china-code-panel" aria-labelledby="china-csp-heading">
                  <header>
                    <h2 id="china-csp-heading">CSP a consultar</h2>
                    <span>{csps.length}</span>
                  </header>
                  <div className="china-code-add-row">
                    <input
                      aria-label="Nuevo código CSP"
                      placeholder="Ingrese código CSP"
                      value={cspDraft}
                      onChange={(event) => setCspDraft(event.target.value)}
                      inputMode="numeric"
                      onKeyDown={(event) => event.key === 'Enter' && (event.preventDefault(), addCsp())}
                    />
                    <button type="button" className="china-add-button" onClick={addCsp} disabled={loading}>Agregar</button>
                  </div>
                  {csps.length ? (
                    <ul className="china-code-list">
                      {csps.map((code, index) => (
                        <li className="china-code-item" key={`${code}-${index}`}>
                          {editingCspIndex === index ? (
                            <input
                              aria-label={`Editar CSP ${index + 1}`}
                              value={editingCspDraft}
                              onChange={(event) => setEditingCspDraft(event.target.value)}
                              inputMode="numeric"
                              autoFocus
                            />
                          ) : <strong>{code}</strong>}
                          <div className="china-code-actions">
                            {editingCspIndex === index ? (
                              <>
                                <MiniIconButton label={`Guardar CSP ${index + 1}`} icon="save" onClick={() => saveCspEdit(index)} />
                                <MiniIconButton label="Cancelar edición" icon="cancel" onClick={() => { setEditingCspIndex(null); setEditingCspDraft(''); setError(''); }} />
                              </>
                            ) : (
                              <>
                                <MiniIconButton label={`Editar CSP ${code}`} icon="edit" onClick={() => { setEditingCspIndex(index); setEditingCspDraft(code); setError(''); }} />
                                <MiniIconButton label={`Eliminar CSP ${code}`} icon="delete" onClick={() => setCsps((current) => current.filter((_, itemIndex) => itemIndex !== index))} />
                              </>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : <p className="china-empty-list">Aún no hay CSP agregados.</p>}
                </section>
              </div>
              <div className="china-submit-row">
                <button type="submit" disabled={loading}>
                  {loading ? 'Consultando fuentes oficiales…' : 'Consultar y generar informe'}
                </button>
              </div>
            </form>

            {error && <div className="china-error" role="alert">{error}</div>}

            {report && (
              <section className="china-report" aria-live="polite">
                <div className="china-report-heading">
                  <div>
                    <span className="china-kicker">Resultado consolidado</span>
                    <h2>{report.status === 'QUEUED' ? 'Informe en cola' : report.status === 'PROCESSING' ? 'Consultando fuentes oficiales' : report.status === 'FAILED' ? 'Informe no completado' : 'Verificaciones oficiales'}</h2>
                  </div>
                  {report.status === 'COMPLETED' && report.pdf_url && (
                    <button className="china-download" type="button" onClick={handleDownload} disabled={downloading}>
                      {downloading ? 'Descargando…' : 'Descargar PDF'}
                    </button>
                  )}
                </div>
                {['QUEUED', 'PROCESSING'].includes(report.status) && (
                  <p className="china-job-status" role="status">
                    {report.status === 'QUEUED' ? 'Tu consulta está esperando turno.' : 'Estamos consultando las fuentes; puedes dejar esta pantalla abierta.'}
                  </p>
                )}
                {report.status === 'COMPLETED' && (
                  <>
                  <div className="china-results-grid">
                  {(report.results?.csgs || (report.results?.csg ? [report.results.csg] : [])).map((result) => (
                    <ResultCard key={result.code} title="Huerto (CSG)" result={result} />
                  ))}
                  {(report.results?.csps || (report.results?.csp?.code ? [report.results.csp] : [])).map((result) => (
                    <ResultCard key={result.code} title="Packing (CSP)" result={result} />
                  ))}
                </div>
                {report.sources?.some((source) => source.status !== 'ok') && (
                  <p className="china-source-warning">
                    Algunas fuentes no pudieron verificarse. Esos resultados se muestran como “No verificado”, no como “No”.
                  </p>
                )}
                  </>
                )}
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default function CherryChinaValidationApp() {
  return (
    <ThemeProvider>
      <CherryChinaValidationContent />
    </ThemeProvider>
  );
}