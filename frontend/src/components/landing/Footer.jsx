import React from 'react';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          {/* About Section */}
          <div className="footer-section">
            <h3>Sobre agrosample</h3>
            <p>
              Plataforma especializada en muestreo agil, impresion automatizada de numeros y control de pallets con impresoras Zebra.
              Diseñada para optimizar operaciones en plantas fruticolas.
            </p>
          </div>

          {/* Features Section */}
          <div className="footer-section">
            <h3>Características</h3>
            <ul className="footer-links">
              <li><a href="#about-system">Muestreo Manual Flexible</a></li>
              <li><a href="#about-system">Diagramas de Pallets</a></li>
              <li><a href="#about-system">Impresoras Zebra</a></li>
              <li><a href="#about-system">Acceso Controlado</a></li>
            </ul>
          </div>

          {/* Links Section */}
          <div className="footer-section">
            <h3>Acceso</h3>
            <ul className="footer-links">
              <li><a href="/login?access=admin">Iniciar Sesión</a></li>
              <li><a href="#about-system">Conocer Más</a></li>
              <li><a href="/">Inicio</a></li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="footer-bottom">
          <p>&copy; 2025 agrosample. Todos los derechos reservados.</p>
          <p className="footer-version">Sistema de Muestreo y Etiquetado v1.0</p>
        </div>
      </div>
    </footer>
  );
}
