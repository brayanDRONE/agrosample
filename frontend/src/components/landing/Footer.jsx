import React from 'react';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          {/* About Section */}
          <div className="footer-section">
            <h3>Acerca del Sistema</h3>
            <p>
              Sistema de Agendamiento del Programa de Pre-embarque coordinado entre el Servicio Agrícola y Ganadero (SAG), 
              USDA-APHIS y la Asociación de Frutas de Chile para garantizar la seguridad agroalimentaria en exportaciones.
            </p>
          </div>

          {/* Contact Section */}
          <div className="footer-section">
            <h3>Contacto SAG</h3>
            <ul className="footer-links">
              <li>Paseo Bulnes 140</li>
              <li>Santiago, Chile</li>
              <li>Teléfono: +56 2 24734000</li>
              <li><a href="mailto:info@sag.gob.cl">info@sag.gob.cl</a></li>
              <li><a href="https://www.sag.gob.cl" target="_blank" rel="noopener noreferrer">www.sag.gob.cl</a></li>
            </ul>
          </div>

          {/* Links Section */}
          <div className="footer-section">
            <h3>Enlaces Rápidos</h3>
            <ul className="footer-links">
              <li><a href="https://www.sag.gob.cl" target="_blank" rel="noopener noreferrer">SAG</a></li>
              <li><a href="https://www.aphis.usda.gov" target="_blank" rel="noopener noreferrer">USDA-APHIS</a></li>
              <li><a href="https://www.frutasdechile.com" target="_blank" rel="noopener noreferrer">Frutas de Chile</a></li>
              <li><a href="/login">Acceso al Sistema</a></li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="footer-bottom">
          <p>&copy; 2025 Sistema de Agendamiento SAG. Todos los derechos reservados.</p>
          <div className="footer-badges">
            <span className="badge">SAG</span>
            <span className="badge">USDA-APHIS</span>
            <span className="badge">Frutas de Chile</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
