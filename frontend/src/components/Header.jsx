/**
 * Header component - Encabezado institucional del sistema
 */

import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import './Header.css';

function Header() {
  const { theme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const companyName = theme?.company_name || user?.establishment?.nombre || 'agrosample';
  const welcomeMessage = theme?.welcome_message || 'Automatización de etiquetas y diagramas adaptables';

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-title">
          <h1>{companyName}</h1>
          {welcomeMessage && (
            <p className="header-subtitle">{welcomeMessage}</p>
          )}
        </div>
        
        <div className="header-actions">
          {user ? (
            <>
              <div className="user-info">
                <div className="user-avatar">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                </div>
                <span className="user-name">{user.username}</span>
              </div>
              <button onClick={handleLogout} className="btn-logout" title="Cerrar Sesión">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd" />
                </svg>
                <span>Cerrar Sesión</span>
              </button>
            </>
          ) : (
            <button onClick={() => navigate('/login?access=admin')} className="btn-logout" title="Acceso Administrador" style={{ background: 'transparent', color: '#10b981', border: '1px solid #10b981' }}>
              <span>Acceso Admin</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
