import React from 'react';
import { Link } from 'react-router-dom';
import './HeroSection.css';

function HeroSection() {
  return (
    <section className="hero-section">
      <div className="hero-background"></div>
      <div className="hero-content">
        <h1 className="hero-title">Simplifica tu muestreo con impresion automatizada y diagramas de pallets adaptables</h1>
        <p className="hero-subtitle">Registra lotes, ingresa números de muestra manualmente e imprime etiquetas Zebra en minutos</p>
        <div className="hero-cta">
          <Link to="/login?access=admin" className="btn-primary-hero">
            Comenzar
          </Link>
          <a href="#about-system" className="btn-secondary-hero">
            Conocer Más
          </a>
        </div>
      </div>
    </section>
  );
}

export default HeroSection;
