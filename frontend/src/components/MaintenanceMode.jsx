/**
 * Página de Mantenimiento - Sistema Temporalmente Deshabilitado
 */

import './MaintenanceMode.css';

function MaintenanceMode() {
  const contactEmail = 'admin@usda.gov';
  const contactPhone = '+1-800-XXX-XXXX';

  return (
    <div className="maintenance-container">
      <div className="maintenance-content">
        {/* Icono de mantenimiento */}
        <div className="maintenance-icon">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>

        {/* Título principal */}
        <h1 className="maintenance-title">
          Sistema Temporalmente Deshabilitado
        </h1>

        {/* Mensaje descriptivo */}
        <p className="maintenance-message">
          La aplicación se encuentra fuera de servicio hasta nuevo aviso.
        </p>

        {/* Sección de información */}
        <div className="maintenance-info">
          <h2>¿Qué sucede?</h2>
          <p>
            Estamos realizando tareas de mantenimiento y actualizaciones para
            mejorar tu experiencia. Durante este tiempo, el acceso a la
            aplicación está temporalmente deshabilitado.
          </p>
        </div>

        {/* Sección de contacto */}
        <div className="maintenance-contact">
          <h3>Para más información, contacta al administrador:</h3>
          <div className="contact-details">
            <div className="contact-item">
              <span className="contact-label">📧 Email:</span>
              <a href={`mailto:${contactEmail}`} className="contact-link">
                {contactEmail}
              </a>
            </div>
            <div className="contact-item">
              <span className="contact-label">📞 Teléfono:</span>
              <a href={`tel:${contactPhone}`} className="contact-link">
                {contactPhone}
              </a>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="maintenance-footer">
          <p>
            Agradecemos tu paciencia. Nos disculpamos por cualquier
            inconveniente.
          </p>
        </div>
      </div>

      {/* Fondo decorativo */}
      <div className="maintenance-background">
        <div className="background-circle circle-1"></div>
        <div className="background-circle circle-2"></div>
        <div className="background-circle circle-3"></div>
      </div>
    </div>
  );
}

export default MaintenanceMode;
