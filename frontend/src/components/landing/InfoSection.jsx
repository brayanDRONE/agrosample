import React from 'react';
import Icon from './Icon';
import './InfoSection.css';

const solutions = [
  {
    icon: 'printer',
    title: 'Muestreo y Etiquetado',
    description: 'Genera muestras, imprime adhesivos personalizados y crea diagramas de pallets en PDF.',
    image: '/Imagen de ChatGPT 17 nov 2026, 12_49_11-1.png',
    imageAlt: 'Adhesivos de muestra junto a un diagrama de pallet'
  },
  {
    icon: 'file',
    title: 'Planilla de Descripción del Lote',
    description: 'Carga tu archivo plano, registra los certificados y genera la planilla lista para presentar al SAG.',
    image: '/Imagen de ChatGPT 17 nov 2026, 12_49_11-2.png',
    imageAlt: 'Vista de una planilla de descripción del lote'
  },
  {
    icon: 'shield',
    title: 'Validación de SDP',
    description: 'Carga tu packing list, valida todos los SDP del lote y obtén un resumen con reporte en PDF.',
    image: '/Imagen de ChatGPT 17 nov 2026, 12_49_12-3.png',
    imageAlt: 'Resumen ilustrativo de registros validados'
  },
  {
    icon: 'cherry',
    title: 'Validación de Cerezas para China',
    description: 'Consulta múltiples CSG y CSP en las páginas del SAG y verifica el cumplimiento de tus productores y establecimientos.',
    image: '/Imagen de ChatGPT 17 nov 2026, 12_49_14-4.png',
    imageAlt: 'Formulario de consulta de códigos CSG y CSP'
  }
];

const reasons = [
  { icon: 'clock', title: 'Ahorro de tiempo', text: 'Automatiza tareas repetitivas.' },
  { icon: 'target', title: 'Mayor precisión', text: 'Reduce errores de digitación.' },
  { icon: 'layers', title: 'Todo en un solo lugar', text: 'Muestreo, documentos y validaciones.' },
  { icon: 'headset', title: 'Soporte y acompañamiento', text: 'Implementación y ayuda continua.' }
];

export default function InfoSection() {
  return (
    <>
      <section id="about-system" className="info-section">
        <div className="info-container">
          <div className="solutions-header">
            <h2 className="info-title">Nuestras Soluciones</h2>
            <p className="info-subtitle">
              Herramientas especializadas para la preparación y control de tus inspecciones.
            </p>
          </div>

          <div className="features-grid">
            {solutions.map((item, index) => (
              <article key={item.title} className="feature-box">
                <span className="feature-number">{String(index + 1).padStart(2, '0')}</span>
                <div className="feature-head">
                  <span className="feature-icon" aria-hidden="true"><Icon name={item.icon} size={26} /></span>
                  <h3 className="feature-title">{item.title}</h3>
                </div>
                <p className="feature-description">{item.description}</p>
                <img className="feature-image" src={item.image} alt={item.imageAlt} loading="lazy" />
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="beneficios" className="why-section">
        <div className="why-container">
          <h2 className="why-title">¿Por qué elegir <span>AgroSample</span>?</h2>
          <div className="why-grid">
            {reasons.map((item) => (
              <div key={item.title} className="why-item">
                <span className="why-icon" aria-hidden="true"><Icon name={item.icon} size={26} /></span>
                <strong>{item.title}</strong>
                <span>{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

export function CtaSection() {
  return (
    <section id="cta" className="cta-section">
      <div className="cta-banner">
        <span className="cta-icon" aria-hidden="true"><Icon name="calendar" size={28} /></span>
        <div className="cta-text">
          <h2>Optimiza la preparación de tus inspecciones</h2>
          <p>Conoce AgroSample en acción y descubre cómo puede apoyar la operación de tu packing o exportadora.</p>
        </div>
        <a href="#contacto" className="cta-button">Solicitar demostración ›</a>
      </div>
    </section>
  );
}
