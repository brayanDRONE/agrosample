import React from 'react';
import './InfoSection.css';

function InfoSection() {
  return (
    <section id="about-system" className="info-section">
      <div className="info-container">

        <h2 className="info-title">Sistema de Automatización de Muestreos</h2>
        <p className="info-subtitle">
          Programa de Pre-embarque SAG / USDA-APHIS / Frutas de Chile
        </p>

        <div className="info-content">
          <p className="info-text">
            El Sistema de Automatización de Muestreos es una plataforma diseñada como
            herramienta de apoyo para optimizar los procesos asociados a las inspecciones
            fitosanitarias en el programa de pre-embarque de frutas destinadas a exportación.
          </p>

          <p className="info-text">
            La plataforma automatiza cálculos de muestreo que tradicionalmente se realizan de
            forma manual, permitiendo a administradores y supervisores generar rápidamente los
            parámetros necesarios para la inspección de lotes, reduciendo tiempos operativos y
            minimizando errores en la determinación de tamaños de muestra.
          </p>

          <p className="info-text">
            El sistema permite configurar especies y parámetros de incremento de muestreo,
            facilitando la preparación del proceso de inspección y la generación automática
            de la documentación requerida para su ejecución.
          </p>

          <p className="info-text">
            La plataforma no almacena información de inspecciones ni resultados operativos,
            funcionando exclusivamente como una herramienta de apoyo para la generación de
            muestreos y emisión de documentación asociada al proceso de inspección.
          </p>
        </div>

        <div className="info-features">
          <div className="feature-card">
            <h4 className="feature-title">✓ Automatización de Muestreos</h4>
            <p className="feature-text">
              Generación automática de parámetros de muestreo utilizados en inspecciones fitosanitarias.
            </p>
          </div>

          <div className="feature-card">
            <h4 className="feature-title">✓ Reducción de Tiempos</h4>
            <p className="feature-text">
              Elimina cálculos manuales y optimiza los tiempos de preparación de inspecciones.
            </p>
          </div>

          <div className="feature-card">
            <h4 className="feature-title">✓ Documentación Automática</h4>
            <p className="feature-text">
              Generación e impresión de documentos necesarios para el proceso de inspección.
            </p>
          </div>

          <div className="feature-card">
            <h4 className="feature-title">✓ Acceso Controlado</h4>
            <p className="feature-text">
              Uso exclusivo para administradores y supervisores autorizados del sistema.
            </p>
          </div>
        </div>

      </div>
    </section>
  );
}

export default InfoSection;
