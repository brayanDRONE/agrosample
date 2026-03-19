/**
 * Login component - Pantalla de inicio de sesión
 */

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Login.css';

function Login({ onLoginSuccess }) {
  const { login, error } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setLocalError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      setLocalError('Por favor complete todos los campos');
      return;
    }

    setLoading(true);
    setLocalError(null);

    const result = await login(formData.username, formData.password);

    if (result.success) {
      onLoginSuccess && onLoginSuccess(result.user);
    } else {
      setLocalError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="login-container">
      {/* Capas de fondo animadas con efecto 3D parallax */}
      <div className="bg-layer bg-layer-1"></div>
      <div className="bg-layer bg-layer-2"></div>
      <div className="bg-layer bg-layer-3"></div>
      <div className="bg-layer bg-layer-4"></div>
      <div className="bg-layer bg-layer-5"></div>
      <div className="bg-layer bg-layer-6"></div>
      <div className="bg-overlay"></div>
      
      <div className="login-card">
        <div className="login-header">
          <div className="login-icon">
            <svg width="48" height="48" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
            </svg>
          </div>
          <h1>agrosample</h1>
          <p>Acceso al sistema</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Usuario</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="Ingrese su usuario"
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Ingrese su contraseña"
              autoComplete="current-password"
            />
          </div>

          {(localError || error) && (
            <div className="error-message">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {localError || error}
            </div>
          )}

          <button 
            type="submit" 
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Iniciando sesión...
              </>
            ) : (
              'Iniciar Sesión'
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>Para acceso, contacte al administrador</p>
        </div>
      </div>
    </div>
  );
}

export default Login;
