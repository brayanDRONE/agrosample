/**
 * AdminDashboard - Panel de control para superadministrador
 * Gestiona establecimientos, suscripciones y estadísticas generales
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/api';
import AdminNavigation, { AdminBrand } from './AdminNavigation';
import './AdminDashboard.css';

function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [establishments, setEstablishments] = useState([]);
  const [establishmentPlans, setEstablishmentPlans] = useState([]);
  const [quotaDrafts, setQuotaDrafts] = useState({});
  const [quotaLoading, setQuotaLoading] = useState(true);
  const [quotaError, setQuotaError] = useState('');
  const [savingPlanId, setSavingPlanId] = useState(null);
  const [pendingEstablishment, setPendingEstablishment] = useState(null);
  const [pendingUsages, setPendingUsages] = useState([]);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Verificar que es superadmin
    if (!user?.is_superadmin) {
      navigate('/muestreo');
      return;
    }
    loadDashboardData();
    loadEstablishments();
    loadPlans();
    
    // Recargar stats cada 30 segundos
    const interval = setInterval(() => {
      loadDashboardData();
      loadEstablishments();
      loadPlans();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setError(null);
      
      const statsData = await apiService.getAdminStats();
      setStats(statsData);
    } catch (err) {
      console.error('Error loading dashboard:', err);
      setError('Error al cargar los datos del dashboard');
    }
  };

  const loadEstablishments = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAllEstablishments();
      setEstablishments(data);
    } catch (err) {
      console.error('Error loading establishments:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadPlans = async () => {
    try {
      setQuotaError('');
      const plans = await apiService.getEstablishmentPlans();
      setEstablishmentPlans(plans);
      setQuotaDrafts(Object.fromEntries(plans.map(({ id, plan }) => [id, plan?.plan || ''])));
    } catch (err) {
      console.error('Error loading plans:', err);
      setQuotaError('No se pudieron cargar los planes.');
    } finally {
      setQuotaLoading(false);
    }
  };

  const updatePlan = async (id, reset = false) => {
    const selected = quotaDrafts[id];
    if (!reset && !selected) {
      setQuotaError('Selecciona un plan.');
      return;
    }
    const message = reset
      ? '¿Reiniciar los usos Free? Las operaciones pendientes se cancelarán.'
      : `¿Asignar o renovar el plan ${selected}? Esto inicia un nuevo período de usos.`;
    if (!window.confirm(message)) return;
    setSavingPlanId(id);
    setQuotaError('');
    try {
      if (reset) await apiService.resetFreeUsage(id);
      else await apiService.assignEstablishmentPlan(id, selected);
      await loadPlans();
    } catch (err) {
      console.error('Error updating plan:', err);
      setQuotaError(err.response?.data?.message || 'No se pudo actualizar el plan.');
    } finally {
      setSavingPlanId(null);
    }
  };

  const loadPendingUsages = async (establishment) => {
    setPendingEstablishment(establishment);
    setPendingLoading(true);
    setQuotaError('');
    try {
      setPendingUsages(await apiService.getPendingPlanUsages(establishment.id));
    } catch (err) {
      console.error('Error loading pending usages:', err);
      setPendingUsages([]);
      setQuotaError('No se pudieron cargar las operaciones pendientes.');
    } finally {
      setPendingLoading(false);
    }
  };

  const resolvePendingUsage = async (usage, succeeded) => {
    const decision = succeeded ? 'contar este uso' : 'liberar este uso';
    if (!window.confirm(`¿Confirmas ${decision}? Verifica primero que la operación ya no esté en curso.`)) return;
    setPendingLoading(true);
    try {
      await apiService.resolvePendingPlanUsage(pendingEstablishment.id, usage.id, succeeded);
      await Promise.all([loadPendingUsages(pendingEstablishment), loadPlans()]);
    } catch (err) {
      console.error('Error resolving pending usage:', err);
      setQuotaError(err.response?.data?.message || 'No se pudo resolver la operación.');
      setPendingLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (loading && !stats) {
    return (
      <div className="dashboard-loading">
        <div className="spinner-large"></div>
        <p>Cargando dashboard...</p>
      </div>
    );
  }

  const StatCard = ({ icon, title, value, color, action }) => (
    <div className={`stat-card stat-${color}`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <h3>{title}</h3>
        <p className="stat-value">{value}</p>
        {action && <button className="stat-link" onClick={action}>{action.label} →</button>}
      </div>
    </div>
  );

  return (
    <div className="admin-dashboard">
      <AdminNavigation current="dashboard" />
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <AdminBrand />
          <div className="header-left">
            <h1>Panel de Administración</h1>
            <p>Gestión de establecimientos y suscripciones</p>
          </div>
          <div className="header-right">
            <div className="user-badge">
              <span className="badge-label">Admin:</span>
              <span className="badge-value">{user?.username}</span>
            </div>
            <button onClick={handleLogout} className="btn btn-secondary btn-sm">
              Salir
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="dashboard-main">
        <div className="dashboard-container">
          {error && (
            <div className="alert alert-error">
              <p>{error}</p>
              <button onClick={loadDashboardData} className="btn btn-sm btn-primary">
                Reintentar
              </button>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="dashboard-tabs">
            <button 
              className="tab-button active"
            >
              Gestión
            </button>
          </div>

          <div className="management-section">
            <h2>Centro de Gestión</h2>
              <div className="management-grid">
                <button 
                  onClick={() => navigate('/admin/establishments')}
                  className="management-card"
                >
                  <div className="card-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M5 21V4h11v17M16 10h3v11M3 21h18M9 8h3M9 12h3M9 16h3" strokeLinecap="round" strokeLinejoin="round" /></svg>
                  </div>
                  <div className="card-content">
                    <h3>Establecimientos</h3>
                    <p>Crear, editar, y eliminar establecimientos</p>
                  </div>
                </button>
                <button 
                  onClick={() => {
                    loadDashboardData();
                    loadEstablishments();
                    loadPlans();
                  }}
                  className="management-card"
                >
                  <div className="card-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M20 7v5h-5M4 17v-5h5M5 9a7 7 0 0 1 12-3l3 3M19 15a7 7 0 0 1-12 3l-3-3" strokeLinecap="round" strokeLinejoin="round" /></svg>
                  </div>
                  <div className="card-content">
                    <h3>Actualizar Datos</h3>
                    <p>Recargar información en tiempo real</p>
                  </div>
                </button>
              </div>

              {/* Establishments List */}
              <div className="establishments-list-section">
                <h3>Establecimientos en el Sistema</h3>
                {establishments && establishments.length > 0 ? (
                  <div className="establishments-table-wrapper">
                    <table className="establishments-table">
                      <thead>
                        <tr>
                          <th>Nombre</th>
                          <th>Exportadora</th>
                          <th>Plan</th>
                          <th>Vence</th>
                          <th>Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {establishments.map((est) => (
                          <tr key={est.id}>
                            <td className="est-name">{est.planta_fruticola}</td>
                            <td>{est.exportadora}</td>
                            <td>
                              {establishmentPlans.find((item) => item.id === est.id)?.plan?.plan || 'Sin asignar'}
                            </td>
                            <td>{establishmentPlans.find((item) => item.id === est.id)?.plan?.expires_at?.slice(0, 10) || '-'}</td>
                            <td className={`status-${est.is_active ? 'active' : 'inactive'}`}>
                              <span className="admin-status-dot" aria-hidden="true"></span>
                              {est.subscription_status === 'SUSPENDED' ? 'Suspendido' : est.is_active ? 'Activo' : 'Inactivo'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="empty-establishments">
                    <p>No hay establecimientos registrados aún</p>
                  </div>
                )}
              </div>

              <section className="user-quotas-section">
                <div className="section-header">
                  <div>
                    <h3>Planes por establecimiento</h3>
                    <p>Asigna un plan, consulta los usos disponibles o reinicia los usos Free.</p>
                  </div>
                </div>
                {quotaError && <div className="alert alert-error" role="alert">{quotaError}</div>}
                {quotaLoading ? (
                  <p className="quota-empty-state">Cargando planes...</p>
                ) : establishmentPlans.length ? (
                  <div className="user-quotas-table-wrapper">
                    <table className="user-quotas-table">
                      <thead>
                        <tr>
                          <th>Establecimiento</th>
                          <th>Plan actual</th>
                          <th>Usos disponibles</th>
                          <th>Asignar plan</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {establishmentPlans.map(({ id, name, plan }) => {
                          return (
                            <tr key={id}>
                              <td><strong>{name}</strong></td>
                              <td>{plan?.plan || 'Sin asignar'}</td>
                              <td>{!plan ? '—' : plan.limit === null ? 'Ilimitados' : `${plan.remaining} de ${plan.limit}`}</td>
                              <td>
                                <select
                                  aria-label={`Plan para ${name}`}
                                  value={quotaDrafts[id] || ''}
                                  onChange={(event) => setQuotaDrafts((current) => ({ ...current, [id]: event.target.value }))}
                                >
                                  <option value="">Seleccionar</option>
                                  <option value="FREE">Free</option>
                                  <option value="STARTER">Starter</option>
                                  <option value="PRO">Pro</option>
                                </select>
                              </td>
                              <td>
                                <button
                                  className="btn btn-primary btn-sm"
                                  type="button"
                                  disabled={savingPlanId === id}
                                  onClick={() => updatePlan(id)}
                                >
                                  Asignar / renovar
                                </button>
                                {plan?.plan === 'FREE' && (
                                  <button className="btn btn-secondary btn-sm" type="button" disabled={savingPlanId === id} onClick={() => updatePlan(id, true)}>
                                    Reiniciar usos
                                  </button>
                                )}
                                <button className="btn btn-secondary btn-sm" type="button" onClick={() => loadPendingUsages({ id, name })}>
                                  Revisar pendientes
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="quota-empty-state">No hay establecimientos disponibles.</p>
                )}
                {pendingEstablishment && (
                  <div className="section-header">
                    <div>
                      <h3>Operaciones pendientes: {pendingEstablishment.name}</h3>
                      <p>Solo se muestran operaciones sin confirmar de más de una hora. Verifica su resultado antes de resolverlas.</p>
                      {pendingLoading ? <p>Cargando...</p> : pendingUsages.length ? pendingUsages.map((usage) => (
                        <div key={usage.id}>
                          <span>{usage.operation === 'sdp' ? 'Validación SDP' : 'Diagrama'} · {usage.user} · {new Date(usage.created_at).toLocaleString('es-CL')} </span>
                          <button className="btn btn-secondary btn-sm" type="button" onClick={() => resolvePendingUsage(usage, true)}>Contar uso</button>
                          <button className="btn btn-secondary btn-sm" type="button" onClick={() => resolvePendingUsage(usage, false)}>Liberar uso</button>
                        </div>
                      )) : <p>No hay operaciones pendientes para revisión.</p>}
                    </div>
                  </div>
                )}
              </section>
            </div>
        </div>
      </main>
    </div>
  );
}

export default AdminDashboard;
