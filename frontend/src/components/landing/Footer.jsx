import React from 'react';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <p>&copy; {new Date().getFullYear()} AgroSample.cl. Todos los derechos reservados.</p>
        <p className="footer-version">Sistema de Muestreo y Etiquetado v1.0</p>
      </div>
    </footer>
  );
}
