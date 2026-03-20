import React from 'react';
import { Link } from 'react-router-dom';
import './HeaderLanding.css';

function HeaderLanding() {
  return (
    <header className="header-landing">
      <div className="header-landing-content">
        <div className="logo-section">
          <div className="logo-placeholder">
            <span className="logo-icon">🌾</span>
          </div>
          <div className="header-text">
            <h1 className="header-title">agrosample</h1>
            <p className="header-subtitle">Impresion automatizada y diagramas adaptables de pallets</p>
          </div>
        </div>
        
        <nav className="header-nav">
          <Link to="/login?access=admin" className="btn-access">
            Acceso
          </Link>
        </nav>
      </div>
    </header>
  );
}

export default HeaderLanding;
