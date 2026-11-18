import React from 'react';
import Icon from './Icon';
import './HeroSection.css';

const highlights = [
  { icon: 'bolt', title: 'Más eficiencia', text: 'Menos trabajo manual' },
  { icon: 'shield', title: 'Menos errores', text: 'Mayor seguridad operativa' },
  { icon: 'chart', title: 'Procesos ordenados', text: 'Documentación lista' },
  { icon: 'leaf', title: 'Diseñado para la industria', text: 'frutícola de Chile' }
];

function HeroSection() {
  return (
    <section id="inicio" className="hero-section">
      <div
        className="hero-banner"
        role="img"
        aria-label="AgroSample en un computador portátil en un entorno de producción agrícola"
      >
        <div className="hero-content">
          <h1 className="hero-title">
            <span>Digitaliza y simplifica</span>
            tus procesos de inspección fitosanitaria
          </h1>
          <p className="hero-subtitle">
            Automatiza el muestreo, genera tus documentos y valida información del SAG de forma rápida, segura y confiable.
          </p>
        </div>
      </div>

      <div className="hero-highlights">
        {highlights.map((item) => (
          <div key={item.title} className="highlight-item">
            <span className="highlight-icon" aria-hidden="true"><Icon name={item.icon} size={30} /></span>
            <div>
              <strong>{item.title}</strong>
              <span>{item.text}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default HeroSection;
