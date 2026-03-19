/**
 * EstablishmentManagement - Gestión de establecimientos
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/api';
import './EstablishmentManagement.css';

function EstablishmentManagement() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [establishments, setEstablishments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState(searchParams.get('filter') || 'all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showRenewModal, setShowRenewModal] = useState(false);
  const [selectedEstablishment, setSelectedEstablishment] = useState(null);
  const [renewDays, setRenewDays] = useState(30);
  const [formData, setFormData] = useState({
    exportadora: '',
    planta_fruticola: '',
    rut: '',
    address: '',
    phone: '',
    email: '',
    encargado_sag: '',
    admin_username: '',
    admin_email: '',
    admin_password: '',
    confirm_password: '',
    admin_sample_label: 'MUESTRA USDA',
    subscription_days: 30
  });

  useEffect(() => {
    loadEstablishments();
  }, [filterType]);

  const loadEstablishments = async () => {
    try {
      setLoading(true);
      setError(null);

      let data;
      if (filterType === 'all') {
        data = await apiService.getAllEstablishments();
      } else {
        data = await apiService.getEstablishmentsByFilter(filterType);
      }

      setEstablishments(data);
    } catch (err) {
      console.error('Error loading establishments:', err);
      setError('Error al cargar los establecimientos');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filter) => {
    setFilterType(filter);
    setSearchParams({ filter });
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    
    // Validar que las contraseñas coincidan
    if (formData.admin_password !== formData.confirm_password) {
      alert('Las contraseñas no coinciden. Por favor verifique.');
      return;
    }
    
    try {
      // Usar el email de contacto como email del admin
      const dataToSend = {
        exportadora: formData.exportadora,
        planta_fruticola: formData.planta_fruticola,
        rut: formData.rut,
        address: formData.address,
        phone: formData.phone,
        email: formData.email,
        encargado_sag: formData.encargado_sag,
        admin_username: formData.admin_username,
        admin_password: formData.admin_password,
        admin_email: formData.email || '',
        admin_sample_label: formData.admin_sample_label || 'MUESTRA USDA',
        subscription_days: formData.subscription_days
      };
      
      await apiService.createEstablishment(dataToSend);
      setShowCreateModal(false);
      resetForm();
      loadEstablishments();
    } catch (err) {
      console.error('Error creating establishment:', err);
      alert('Error al crear el establecimiento');
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    
    // Validar contraseñas si se está cambiando
    if (formData.admin_password && formData.admin_password !== formData.confirm_password) {
      alert('Las contraseñas no coinciden. Por favor verifique.');
      return;
    }
    
    try {
      const dataToSend = {
        exportadora: formData.exportadora,
        planta_fruticola: formData.planta_fruticola,
        rut: formData.rut,
        address: formData.address,
        phone: formData.phone,
        email: formData.email,
        encargado_sag: formData.encargado_sag
      };
      
      // Solo agregar credenciales si están siendo modificadas
      if (formData.admin_username) dataToSend.admin_username = formData.admin_username;
      if (formData.admin_password) dataToSend.admin_password = formData.admin_password;
      if (formData.admin_email) dataToSend.admin_email = formData.admin_email;
      
      await apiService.updateEstablishment(selectedEstablishment.id, dataToSend);
      setShowEditModal(false);
      resetForm();
      setSelectedEstablishment(null);
      loadEstablishments();
    } catch (err) {
      console.error('Error updating establishment:', err);
      alert('Error al actualizar el establecimiento');
    }
  };

  const handleRenewSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiService.renewSubscription(selectedEstablishment.id, renewDays);
      setShowRenewModal(false);
      setSelectedEstablishment(null);
      setRenewDays(30);
      loadEstablishments();
    } catch (err) {
      console.error('Error renewing subscription:', err);
      alert('Error al renovar la suscripción');
    }
  };

  const handleSuspend = async (id) => {
    if (!window.confirm('¿Está seguro de suspender este establecimiento?')) return;
    try {
      await apiService.suspendEstablishment(id);
      loadEstablishments();
    } catch (err) {
      console.error('Error suspending establishment:', err);
      alert('Error al suspender el establecimiento');
    }
  };

  const handleActivate = async (id) => {
    try {
      await apiService.activateEstablishment(id);
      loadEstablishments();
    } catch (err) {
      console.error('Error activating establishment:', err);
      alert('Error al activar el establecimiento');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este establecimiento? Esta acción no se puede deshacer.')) return;
    try {
      await apiService.deleteEstablishment(id);
      loadEstablishments();
    } catch (err) {
      console.error('Error deleting establishment:', err);
      alert('Error al eliminar el establecimiento');
    }
  };

  const openEditModal = (establishment) => {
    setSelectedEstablishment(establishment);
    setFormData({
      exportadora: establishment.exportadora || '',
      planta_fruticola: establishment.planta_fruticola || '',
      rut: establishment.rut || '',
      address: establishment.address || '',
      phone: establishment.phone || '',
      email: establishment.email || '',
      encargado_sag: establishment.encargado_sag || '',
      admin_username: '',
      admin_email: '',
      admin_password: '',
      confirm_password: '',
      admin_sample_label: 'MUESTRA USDA',
      subscription_days: 30
    });
    setShowEditModal(true);
  };

  const openRenewModal = (establishment) => {
    setSelectedEstablishment(establishment);
    setShowRenewModal(true);
  };

  const resetForm = () => {
    setFormData({
      exportadora: '',
      planta_fruticola: '',
      rut: '',
      address: '',
      phone: '',
      email: '',
      encargado_sag: '',
      admin_username: '',
      admin_email: '',
      admin_password: '',
      confirm_password: '',
      admin_sample_label: 'MUESTRA USDA',
      subscription_days: 30
    });
  };

  const getStatusBadge = (establishment) => {
    if (establishment.subscription_status === 'SUSPENDED') {
      return <span className="badge badge-suspended">Suspendido</span>;
    }
    if (establishment.subscription_status === 'EXPIRED') {
      return <span className="badge badge-expired">Expirado</span>;
    }
    if (establishment.is_expiring_soon) {
      return <span className="badge badge-expiring">Por vencer</span>;
    }
    return <span className="badge badge-active">Activo</span>;
  };

  return (
    <div className="establishment-management">
      {/* Header */}
      <header className="page-header">
        <div className="header-content">
          <div className="header-left">
            <button onClick={() => navigate('/admin')} className="btn-back">
              ← Volver al Dashboard
            </button>
            <h1>Gestión de Establecimientos</h1>
          </div>
          <div className="header-right">
            <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
              + Nuevo Establecimiento
            </button>
            <button onClick={() => { logout(); navigate('/login'); }} className="btn btn-secondary">
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      {/* Filters */}
      <div className="filters">
        <button
          className={`filter-btn ${filterType === 'all' ? 'active' : ''}`}
          onClick={() => handleFilterChange('all')}
        >
          Todos
        </button>
        <button
          className={`filter-btn ${filterType === 'active' ? 'active' : ''}`}
          onClick={() => handleFilterChange('active')}
        >
          Activos
        </button>
        <button
          className={`filter-btn ${filterType === 'expiring_soon' ? 'active' : ''}`}
          onClick={() => handleFilterChange('expiring_soon')}
        >
          Por Vencer
        </button>
        <button
          className={`filter-btn ${filterType === 'expired' ? 'active' : ''}`}
          onClick={() => handleFilterChange('expired')}
        >
          Expirados
        </button>
      </div>

      {/* Main Content */}
      <main className="page-main">
        {loading ? (
          <div className="loading-state">
            <div className="spinner-large"></div>
            <p>Cargando establecimientos...</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <p>{error}</p>
            <button onClick={loadEstablishments} className="btn btn-primary">
              Reintentar
            </button>
          </div>
        ) : establishments.length === 0 ? (
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 20 20" fill="currentColor">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
            </svg>
            <h3>No hay establecimientos</h3>
            <p>Usa el botón "Nuevo Establecimiento" en la parte superior para crear uno</p>
          </div>
        ) : (
          <div className="establishments-table-wrapper">
            <table className="establishments-table">
              <thead>
                <tr>
                  <th>Planta</th>
                  <th>Exportadora</th>
                  <th>RUT</th>
                  <th>Encargado SAG</th>
                  <th>Usuario Admin</th>
                  <th>Teléfono</th>
                  <th>Estado</th>
                  <th>Vence en</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {establishments.map((est) => (
                  <tr key={est.id}>
                    <td>
                      <div className="establishment-name">
                        <strong>{est.planta_fruticola}</strong>
                        <small>{est.license_key}</small>
                      </div>
                    </td>
                    <td>{est.exportadora || '-'}</td>
                    <td>{est.rut || '-'}</td>
                    <td>{est.encargado_sag || '-'}</td>
                    <td>{est.admin_user?.username || 'Sin asignar'}</td>
                    <td>{est.phone || '-'}</td>
                    <td>{getStatusBadge(est)}</td>
                    <td>
                      {est.days_until_expiry !== null && est.days_until_expiry > 0 ? (
                        <span className={est.is_expiring_soon ? 'days-warning' : 'days-normal'}>
                          {est.days_until_expiry} días
                        </span>
                      ) : (
                        <span className="days-expired">Expirado</span>
                      )}
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          onClick={() => openEditModal(est)}
                          className="btn-icon"
                          title="Editar"
                        >
                          <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => openRenewModal(est)}
                          className="btn-icon btn-success"
                          title="Renovar Suscripción"
                        >
                          <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                          </svg>
                        </button>
                        <button
                          onClick={() => navigate(`/admin/themes/${est.id}`)}
                          className="btn-icon btn-info"
                          title="Personalizar Tema"
                        >
                          <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clipRule="evenodd" />
                          </svg>
                        </button>
                        {est.subscription_status === 'ACTIVE' ? (
                          <button
                            onClick={() => handleSuspend(est.id)}
                            className="btn-icon btn-warning"
                            title="Suspender"
                          >
                            <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clipRule="evenodd" />
                            </svg>
                          </button>
                        ) : (
                          <button
                            onClick={() => handleActivate(est.id)}
                            className="btn-icon btn-success"
                            title="Activar"
                          >
                            <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(est.id)}
                          className="btn-icon btn-danger"
                          title="Eliminar"
                        >
                          <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Nuevo Establecimiento</h2>
              <button onClick={() => setShowCreateModal(false)} className="btn-close">×</button>
            </div>
            <form onSubmit={handleCreateSubmit} className="modal-body">
              <div className="form-section-title">Información de la Empresa</div>
              <div className="form-grid">
                <div className="form-group">
                  <label>Exportadora *</label>
                  <input
                    type="text"
                    value={formData.exportadora}
                    onChange={(e) => setFormData({ ...formData, exportadora: e.target.value })}
                    placeholder="Ej: Frutas del Sur S.A."
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Planta Frutícola *</label>
                  <input
                    type="text"
                    value={formData.planta_fruticola}
                    onChange={(e) => setFormData({ ...formData, planta_fruticola: e.target.value })}
                    placeholder="Ej: Planta Procesadora Los Andes"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>RUT de la Empresa *</label>
                  <input
                    type="text"
                    value={formData.rut}
                    onChange={(e) => setFormData({ ...formData, rut: e.target.value })}
                    placeholder="Ej: 76.123.456-7"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Dirección</label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    placeholder="Ej: Camino a Melipilla Km 32"
                  />
                </div>
                <div className="form-group">
                  <label>Teléfono de Contacto *</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="Ej: +56 9 1234 5678"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Email de Contacto</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="contacto@empresa.cl"
                  />
                </div>
                <div className="form-group">
                  <label>Encargado Área SAG *</label>
                  <input
                    type="text"
                    value={formData.encargado_sag}
                    onChange={(e) => setFormData({ ...formData, encargado_sag: e.target.value })}
                    placeholder="Ej: Juan Pérez González"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Días de Suscripción *</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.subscription_days}
                    onChange={(e) => setFormData({ ...formData, subscription_days: parseInt(e.target.value) })}
                    required
                  />
                </div>
              </div>

              <div className="form-section-title">Credenciales de Acceso al Sistema</div>
              <div className="form-grid">
                <div className="form-group">
                  <label>Nombre de Usuario para Login *</label>
                  <input
                    type="text"
                    value={formData.admin_username}
                    onChange={(e) => setFormData({ ...formData, admin_username: e.target.value })}
                    placeholder="usuario_establecimiento"
                    required
                  />
                  <small className="field-hint">Este será el usuario para iniciar sesión</small>
                </div>
                <div className="form-group">
                  <label>Contraseña de Acceso *</label>
                  <input
                    type="password"
                    value={formData.admin_password}
                    onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                    placeholder="Mínimo 8 caracteres"
                    required
                  />
                  <small className="field-hint">Contraseña para acceder al sistema</small>
                </div>
                <div className="form-group">
                  <label>Repetir Contraseña *</label>
                  <input
                    type="password"
                    value={formData.confirm_password}
                    onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                    placeholder="Repita la contraseña"
                    required
                  />
                  <small className="field-hint">Debe coincidir con la contraseña anterior</small>
                </div>
                <div className="form-group">
                  <label>Texto de Etiqueta de Muestra *</label>
                  <input
                    type="text"
                    value={formData.admin_sample_label}
                    onChange={(e) => setFormData({ ...formData, admin_sample_label: e.target.value })}
                    placeholder="Ej: AGROSAMPLE CALIDAD"
                    required
                  />
                  <small className="field-hint">Este texto reemplaza MUESTRA USDA en la impresión de etiquetas</small>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn btn-secondary">
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  Crear Establecimiento
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedEstablishment && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Editar Establecimiento</h2>
              <button onClick={() => setShowEditModal(false)} className="btn-close">×</button>
            </div>
            <form onSubmit={handleEditSubmit} className="modal-body">
              <div className="form-section-title">Información de la Empresa</div>
              <div className="form-grid">
                <div className="form-group">
                  <label>Exportadora</label>
                  <input
                    type="text"
                    value={formData.exportadora}
                    onChange={(e) => setFormData({ ...formData, exportadora: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Planta Frutícola *</label>
                  <input
                    type="text"
                    value={formData.planta_fruticola}
                    onChange={(e) => setFormData({ ...formData, planta_fruticola: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>RUT de la Empresa</label>
                  <input
                    type="text"
                    value={formData.rut}
                    onChange={(e) => setFormData({ ...formData, rut: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Dirección</label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Teléfono de Contacto</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Email de Contacto</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Encargado Área SAG</label>
                  <input
                    type="text"
                    value={formData.encargado_sag}
                    onChange={(e) => setFormData({ ...formData, encargado_sag: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-section-title">Cambiar Contraseña de Acceso</div>
              <p className="form-section-note">Complete estos campos solo si desea asignar una nueva contraseña</p>
              <div className="form-grid">
                <div className="form-group">
                  <label>Nueva Contraseña</label>
                  <input
                    type="password"
                    value={formData.admin_password}
                    onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                    placeholder="Dejar vacío para mantener la actual"
                  />
                  <small className="field-hint">Mínimo 8 caracteres</small>
                </div>
                <div className="form-group">
                  <label>Repetir Nueva Contraseña</label>
                  <input
                    type="password"
                    value={formData.confirm_password}
                    onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                    placeholder="Repita la nueva contraseña"
                  />
                  <small className="field-hint">Debe coincidir con la contraseña anterior</small>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowEditModal(false)} className="btn btn-secondary">
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  Guardar Cambios
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Renew Modal */}
      {showRenewModal && selectedEstablishment && (
        <div className="modal-overlay" onClick={() => setShowRenewModal(false)}>
          <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Renovar Suscripción</h2>
              <button onClick={() => setShowRenewModal(false)} className="btn-close">×</button>
            </div>
            <form onSubmit={handleRenewSubmit} className="modal-body">
              <p>Renovar suscripción de: <strong>{selectedEstablishment.nombre}</strong></p>
              <div className="form-group">
                <label>Días a agregar</label>
                <input
                  type="number"
                  min="1"
                  value={renewDays}
                  onChange={(e) => setRenewDays(parseInt(e.target.value))}
                  required
                />
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setShowRenewModal(false)} className="btn btn-secondary">
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  Renovar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default EstablishmentManagement;
