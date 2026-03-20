/**
 * AdminDashboard - Panel de control para superadministrador
 * Gestiona establecimientos, suscripciones y estadísticas generales
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/api';
import './AdminDashboard.css';

function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [establishments, setEstablishments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('management');

  useEffect(() => {
    // Verificar que es superadmin
    if (!user?.is_superadmin) {
      navigate('/muestreo');
      return;
    }
    loadDashboardData();
    loadEstablishments();
    
    // Recargar stats cada 30 segundos
    const interval = setInterval(() => {
      loadDashboardData();
      loadEstablishments();
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
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <h1>🏢 Panel de Administración</h1>
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
              🔧 Gestión
            </button>
          </div>

          <div className="management-section">
            <h2>Centro de Gestión</h2>
              <div className="management-grid">
                <button 
                  onClick={() => navigate('/admin/establishments')}
                  className="management-card"
                >
                  <div className="card-icon">🏢</div>
                  <div className="card-content">
                    <h3>Establecimientos</h3>
                    <p>Crear, editar, y eliminar establecimientos</p>
                  </div>
                </button>
                <button 
                  onClick={loadDashboardData}
                  className="management-card"
                >
                  <div className="card-icon">🔄</div>
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
                          <th>Suscripción</th>
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
                              <span className={`status-badge status-${est.subscription_status.toLowerCase()}`}>
                                {est.subscription_status === 'ACTIVE' ? '✅ Activa' : 
                                 est.subscription_status === 'EXPIRED' ? '❌ Expirada' : 
                                 '⏸️ Suspendida'}
                              </span>
                            </td>
                            <td>{est.subscription_expiry || '-'}</td>
                            <td className={`status-${est.is_active ? 'active' : 'inactive'}`}>
                              {est.is_active ? '🟢 Activo' : '🔴 Inactivo'}
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
            </div>
        </div>
      </main>
    </div>
  );
}

export default AdminDashboard;
