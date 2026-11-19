import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/api';
import AdminNavigation, { AdminBrand } from './AdminNavigation';
import './AdminProfile.css';

function getErrorMessage(error) {
  const responseData = error.response?.data;
  if (!responseData) return 'No se pudieron actualizar las credenciales.';
  if (typeof responseData.detail === 'string') return responseData.detail;
  const firstMessage = Object.values(responseData)
    .flat()
    .find((message) => typeof message === 'string');
  return firstMessage || 'No se pudieron actualizar las credenciales.';
}

function AdminProfile() {
  const { user, logout, updateUser } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: user?.username || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    const hasPasswordInput = formData.newPassword || formData.confirmPassword;

    try {
      const result = await apiService.updateCurrentUserCredentials({
        username: formData.username,
        current_password: formData.currentPassword,
        ...(hasPasswordInput ? {
          new_password: formData.newPassword,
          confirm_password: formData.confirmPassword,
        } : {}),
      });

      if (result.password_changed) {
        logout();
        navigate('/login?access=admin', {
          replace: true,
          state: { credentialsUpdated: true },
        });
        return;
      }

      updateUser(result.user);
      setFormData({
        username: result.user.username,
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
      setSuccess('Nombre de usuario actualizado correctamente.');
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="admin-profile-page">
      <AdminNavigation current="profile" />
      <header className="admin-profile-header">
        <div className="admin-profile-header-inner">
          <AdminBrand />
          <div className="admin-profile-heading">
            <h1>Perfil de administrador</h1>
            <p>Actualiza tu nombre de usuario y contraseña.</p>
          </div>
          <div className="admin-profile-account">
            <span>Admin: {user?.username}</span>
            <button type="button" onClick={handleLogout}>Salir</button>
          </div>
        </div>
      </header>

      <main className="admin-profile-main">
        <section className="admin-profile-card">
          <h2>Credenciales de acceso</h2>
          <p className="admin-profile-description">
            Confirma tu contraseña actual para guardar los cambios. Deja los campos de contraseña nueva vacíos si solo quieres cambiar tu usuario.
          </p>

          <form onSubmit={handleSubmit} className="admin-profile-form">
            <div className="admin-profile-field">
              <label htmlFor="admin-username">Nombre de usuario</label>
              <input
                autoComplete="username"
                id="admin-username"
                name="username"
                onChange={handleChange}
                required
                value={formData.username}
              />
            </div>

            <div className="admin-profile-field">
              <label htmlFor="admin-current-password">Contraseña actual</label>
              <input
                autoComplete="current-password"
                id="admin-current-password"
                name="currentPassword"
                onChange={handleChange}
                required
                type="password"
                value={formData.currentPassword}
              />
            </div>

            <div className="admin-profile-field">
              <label htmlFor="admin-new-password">Nueva contraseña</label>
              <input
                autoComplete="new-password"
                id="admin-new-password"
                name="newPassword"
                onChange={handleChange}
                type="password"
                value={formData.newPassword}
              />
            </div>

            <div className="admin-profile-field">
              <label htmlFor="admin-confirm-password">Confirmar nueva contraseña</label>
              <input
                autoComplete="new-password"
                id="admin-confirm-password"
                name="confirmPassword"
                onChange={handleChange}
                type="password"
                value={formData.confirmPassword}
              />
            </div>

            {error && <div className="admin-profile-message error" role="alert">{error}</div>}
            {success && <div className="admin-profile-message success" role="status">{success}</div>}

            <button className="admin-profile-submit" disabled={loading} type="submit">
              {loading ? 'Guardando...' : 'Guardar cambios'}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

export default AdminProfile;
