import React from 'react';
import './InfoSection.css';

function InfoSection() {
  const features = [
    {
      icon: '📋',
      title: 'Registro de Lotes',
      description: 'Ingresa números de lote y cantidad de pallets de forma rápida y sencilla.'
    },
    {
      icon: '🔢',
      title: 'Muestreo Manual',
      description: 'Define números de muestra manualmente con máxima flexibilidad operativa.'
    },
    {
      icon: '📊',
      title: 'Diagramas Visuales',
      description: 'Visualiza pallets con números marcados automáticamente en diagramas.'
    },
    {
      icon: '🖨️',
      title: 'Impresoras Zebra',
      description: 'Imprime etiquetas profesionales con texto personalizado por usuario.'
    }
  ];

  return (
    <section id="about-system" className="info-section">
      <div className="info-container">
        <div className="section-header">
          <h2 className="info-title">¿Cómo Funciona agrosample?</h2>
          <p className="info-subtitle">
            Flujo simplificado de muestreo y control de pallets
          </p>
        </div>

        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-box">
              <div className="feature-icon">{feature.icon}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>

        <div className="benefits-section">
          <h3 className="benefits-title">Ventajas del Sistema</h3>
          <div className="benefits-grid">
            <div className="benefit-item">
              <div className="benefit-check">✓</div>
              <div>
                <h4>Operación Flexible</h4>
                <p>Adaptable a diferentes procesos y necesidades de muestreo</p>
              </div>
            </div>
            <div className="benefit-item">
              <div className="benefit-check">✓</div>
              <div>
                <h4>Errores Reducidos</h4>
                <p>Validación integrada en cada paso del proceso</p>
              </div>
            </div>
            <div className="benefit-item">
              <div className="benefit-check">✓</div>
              <div>
                <h4>Trazabilidad Total</h4>
                <p>Registro completo de lotes, muestras y etiquetas impresas</p>
              </div>
            </div>
            <div className="benefit-item">
              <div className="benefit-check">✓</div>
              <div>
                <h4>Acceso Controlado</h4>
                <p>Seguro con autenticación y personalización por usuario</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default InfoSection;
