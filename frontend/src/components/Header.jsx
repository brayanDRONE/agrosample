/**
 * Header component - Encabezado institucional del sistema
 */

import { useLocation, useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import './Header.css';

function Header() {
  const { theme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const companyName = theme?.company_name || user?.establishment?.nombre || 'agrosample';

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-brand">
          <div className="header-brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path d="M27.5 4.5C16 4.5 8.5 9.2 7.1 17.1c-.6 3.2.7 5.7 3.3 6.2 3.2.6 6.1-1.6 7.6-5.3 1.5-3.6 4.3-7.7 9.5-13.5Z" fill="currentColor" />
              <path d="M5 27c4.2-5.7 8.6-8.6 14.4-10.7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
          <div className="header-title">
            <h1>Agro<span>Sample</span>.cl</h1>
            <p className="header-company-name">{companyName}</p>
          </div>
        </div>
        
        {user && (
          <nav className="header-nav" aria-label="Navegación principal">
            <button type="button" className={`nav-pill${pathname === '/dashboard' ? ' active' : ''}`} onClick={handleBackToDashboard}>
              Inicio
            </button>
            <button type="button" className={`nav-pill${pathname === '/muestreo' ? ' active' : ''}`} onClick={() => navigate('/muestreo')}>
              Muestreo
            </button>
            <div className="nav-dropdown">
              <button type="button" className={`nav-pill${pathname === '/planilla-descripcion' ? ' active' : ''}`}>
                Documentos <span className="nav-caret" aria-hidden="true">⌄</span>
              </button>
              <div className="nav-menu">
                <button type="button" onClick={() => navigate('/planilla-descripcion')}>Planilla de Descripción del Lote</button>
              </div>
            </div>
            <div className="nav-dropdown">
              <button type="button" className={`nav-pill${pathname === '/validacion-sdp' || pathname === '/validacion-cereza-china' ? ' active' : ''}`}>
                Validaciones <span className="nav-caret" aria-hidden="true">⌄</span>
              </button>
              <div className="nav-menu">
                <button type="button" onClick={() => navigate('/validacion-sdp')}>Validación de SDP</button>
                <button type="button" onClick={() => navigate('/validacion-cereza-china')}>Cereza para China</button>
              </div>
            </div>
          </nav>
        )}

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
