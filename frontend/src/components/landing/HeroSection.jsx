import React from 'react';
import { Link } from 'react-router-dom';
import './HeroSection.css';

function HeroSection() {
  return (
    <section className="hero-section">
      <div className="hero-content">
        <h2 className="hero-title">BIENVENIDO/BIENVENIDA</h2>
        <p className="hero-subtitle">Al Sistema de Gestión Documental SAG/USDA</p>
        <Link to="/muestreo" className="btn-primary-hero">
          Iniciar Muestreo
        </Link>
      </div>
    </section>
  );
}

export default HeroSection;
