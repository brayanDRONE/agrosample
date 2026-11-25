import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './HeaderLanding.css';

const NAV = [
  { hash: '', label: 'Inicio' },
  { hash: '#videos', label: 'Videos' },
  { hash: '#planes', label: 'Planes' },
  { hash: '#contacto', label: 'Contacto' }
];

function HeaderLanding() {
  const { hash } = useLocation();
  const current = NAV.some((item) => item.hash === hash) ? hash : '';
  return (
    <header className="header-landing">
      <div className="header-landing-content">
        <Link to="/" className="logo-section">
          <div className="logo-placeholder">
            <svg className="logo-icon" viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <path d="M27.5 4.5C16 4.5 8.5 9.2 7.1 17.1c-.6 3.2.7 5.7 3.3 6.2 3.2.6 6.1-1.6 7.6-5.3 1.5-3.6 4.3-7.7 9.5-13.5Z" fill="currentColor" />
              <path d="M5 27c4.2-5.7 8.6-8.6 14.4-10.7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
          <h1 className="header-title">Agro<span>Sample</span>.cl</h1>
          <p className="header-subtitle">Soluciones digitales<br />para la agroexportación</p>
        </Link>

        <nav className="header-nav">
          {NAV.map((item) => (
            <Link key={item.label} to={`/${item.hash}`} className={`nav-link${current === item.hash ? ' active' : ''}`}>{item.label}</Link>
          ))}
          <Link to="/login?access=admin" className="btn-access">
            Acceso
          </Link>
        </nav>
      </div>
    </header>
  );
}

export default HeaderLanding;
