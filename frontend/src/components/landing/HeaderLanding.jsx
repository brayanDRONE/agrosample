import React from 'react';
import { Link } from 'react-router-dom';
import './HeaderLanding.css';

function HeaderLanding() {
  return (
    <header className="header-landing">
      <div className="container">
        <div className="header-landing-content">
          <div className="logo-section">
            <div className="logo-placeholder">
              <span className="logo-text">SAG</span>
            </div>
            <div className="header-text">
              <h1 className="header-title">Sistema Documental de Muestreo</h1>
              <p className="header-subtitle">Sitios de Inspección</p>
            </div>
          </div>
          
          <nav className="header-nav">
            <Link to="/login" className="btn-access">
              Acceso Administrador
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}

export default HeaderLanding;
