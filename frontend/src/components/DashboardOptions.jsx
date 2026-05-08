/**
 * DashboardOptions - Pantalla de selección de opciones post-login
 */

import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ThemeProvider } from '../contexts/ThemeContext';
import Header from './Header';
import './DashboardOptions.css';

function DashboardOptionsContent() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleMuestreo = () => {
    navigate('/muestreo');
  };

  const handlePlanillaDescripcion = () => {
    navigate('/planilla-descripcion');
  };

  return (
    <div className="app">
      <Header />
      
      <main className="main-container">
        <div className="content-wrapper">
          <div className="dashboard-container">
            <div className="dashboard-header">
              <h1>¿Qué desea realizar hoy?</h1>
              <p>Seleccione una opción para continuar</p>
            </div>

            <div className="options-grid">
              {/* Opción: Muestreo */}
              <div 
                className="option-card muestreo-card"
                onClick={handleMuestreo}
                role="button"
                tabIndex="0"
                onKeyPress={(e) => e.key === 'Enter' && handleMuestreo()}
              >
                <div className="option-icon muestreo-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                </div>
                <div className="option-content">
                  <h2>Realizar Muestreo</h2>
                  <p>Ingrese los datos del producto a muestrear y obtenga el resultado de inspección</p>
                </div>
                <div className="option-arrow">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </div>
              </div>

              {/* Opción: Planilla de Descripción de Lote */}
              <div 
                className="option-card planilla-card"
                onClick={handlePlanillaDescripcion}
                role="button"
                tabIndex="0"
                onKeyPress={(e) => e.key === 'Enter' && handlePlanillaDescripcion()}
              >
                <div className="option-icon planilla-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 12h6m-6 4h6M3 3h18a2 2 0 012 2v14a2 2 0 01-2 2H3a2 2 0 01-2-2V5a2 2 0 012-2z" />
                  </svg>
                </div>
                <div className="option-content">
                  <h2>Generar Planilla de Descripción de Lote</h2>
                  <p>Cargue archivo de lote (.INS) y genere la planilla de descripción con certificados</p>
                </div>
                <div className="option-arrow">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function DashboardOptions() {
  return (
    <ThemeProvider>
      <DashboardOptionsContent />
    </ThemeProvider>
  );
}

export default DashboardOptions;
