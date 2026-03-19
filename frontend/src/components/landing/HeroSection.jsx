import React from 'react';
import { Link } from 'react-router-dom';
import './HeroSection.css';

function HeroSection() {
  return (
    <section className="hero-section">
      <div className="hero-background"></div>
      <div className="hero-content">
        <div className="hero-badge">✨ Sistema Moderno de Muestreo</div>
        <h1 className="hero-title">Muestreo Ágil y Control de Pallets</h1>
        <p className="hero-subtitle">Registra lotes, ingresa números de muestra manualmente e imprime etiquetas Zebra en minutos</p>
        <div className="hero-cta">
          <Link to="/login" className="btn-primary-hero">
            Comenzar
          </Link>
          <a href="#about-system" className="btn-secondary-hero">
            Conocer Más
          </a>
        </div>
        <div className="hero-stats">
          <div className="stat-item">
            <span className="stat-number">100%</span>
            <span className="stat-label">Muestreo Manual</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">∞</span>
            <span className="stat-label">Escalabilidad</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">0s</span>
            <span className="stat-label">Setup</span>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HeroSection;
