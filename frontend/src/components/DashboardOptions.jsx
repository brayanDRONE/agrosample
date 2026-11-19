/**
 * DashboardOptions - Pantalla de selección de opciones post-login
 */

import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { ThemeProvider } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import Header from './Header';
import muestreoImg from '../images/dash-muestreo.jpg';
import planillaImg from '../images/dash-planilla.jpg';
import sdpImg from '../images/dash-sdp.jpg';
import cerezaImg from '../images/dash-cereza.jpg';
import './DashboardOptions.css';

const ICONS = {
  muestreo: (
    <path d="M4 6v12M7 6v12M10 6v12M14 6v12M17 6v12M20 6v12" />
  ),
  planilla: (
    <>
      <path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z" />
      <path d="M14 3v5h5M9 13h6M9 17h6" />
    </>
  ),
  sdp: (
    <>
      <path d="M12 3c2.2 2.1 4.1 2.8 7 2.8v5.1c0 4.3-2.9 7.9-7 9.1-4.1-1.2-7-4.8-7-9.1V5.8c2.9 0 4.8-.7 7-2.8z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  cereza: (
    <>
      <circle cx="8" cy="17" r="3.5" />
      <circle cx="16.5" cy="16" r="3.5" />
      <path d="M8 13.5C8 9 10 6 14 4M16.5 12.5C16 9 15 6 14 4" />
    </>
  )
};

const OPTIONS = [
  {
    key: 'muestreo',
    path: '/muestreo',
    title: 'Realizar Muestreo',
    text: 'Ingresa los datos del producto a muestrear, obtén los números, imprime adhesivos y genera el diagrama de pallets.',
    image: muestreoImg,
    alt: 'Adhesivo de muestra impreso con número de lote'
  },
  {
    key: 'planilla',
    path: '/planilla-descripcion',
    title: 'Generar Planilla de Descripción del Lote',
    text: 'Carga el archivo de lote (LINS), registra los certificados y genera la planilla lista para presentar al SAG.',
    image: planillaImg,
    alt: 'Planilla de descripción del lote'
  },
  {
    key: 'sdp',
    path: '/validacion-sdp',
    title: 'Validación de SDP',
    text: 'Carga tu packing list, valida todos los SDP del lote y obtén un resumen con reporte en PDF.',
    image: sdpImg,
    alt: 'Resumen de validación de SDP'
  },
  {
    key: 'cereza',
    path: '/validacion-cereza-china',
    title: 'Validar Cereza para China',
    text: 'Consulta múltiples CSG y CSP en las páginas del SAG y verifica el cumplimiento de tus productores y establecimientos.',
    image: cerezaImg,
    alt: 'Cerezas con gotas de agua'
  }
];

function DashboardOptionsContent() {
  const navigate = useNavigate();
  const { user, isSuperAdmin } = useAuth();
  const [plan, setPlan] = useState(null);
  const [planLoading, setPlanLoading] = useState(true);
  const [planError, setPlanError] = useState('');

  useEffect(() => {
    if (isSuperAdmin() || !user?.establishment) return;
    apiService.getAccountPlan().then(setPlan).catch((error) => {
      console.error('Error al consultar el plan:', error);
      setPlanError('No se pudo consultar el plan.');
    }).finally(() => setPlanLoading(false));
  }, [user]);

  return (
    <div className="app dashboard-app">
      <Header />

      <main className="main-container">
        <div className="content-wrapper">
          <div className="dashboard-container">
            <div className="dashboard-header">
              <h1>¿Qué deseas realizar hoy?</h1>
              <p>Selecciona una solución para comenzar.</p>
              {!isSuperAdmin() && (
                <p role="status">
                  {planError || (planLoading ? 'Consultando plan...' : plan
                    ? `Plan ${plan.plan}: ${plan.remaining === null ? 'usos ilimitados' : `${plan.remaining} de ${plan.limit} usos disponibles`}`
                    : 'Sin plan asignado. Contacta al administrador.')}
                </p>
              )}
            </div>

            <div className="options-grid">
              {OPTIONS.map((option) => (
                <div
                  key={option.key}
                  className={`option-card ${option.key}-card`}
                  onClick={() => navigate(option.path)}
                  role="button"
                  tabIndex="0"
                  onKeyDown={(e) => e.key === 'Enter' && navigate(option.path)}
                >
                  <div className="option-main">
                    <div className="option-title-row">
                      <span className={`option-icon ${option.key}-icon`}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          {ICONS[option.key]}
                        </svg>
                      </span>
                      <h2>{option.title}</h2>
                    </div>
                    <p>{option.text}</p>
                    <span className="option-arrow" aria-hidden="true">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M5 12h14M13 6l6 6-6 6" />
                      </svg>
                    </span>
                  </div>
                  <img className="option-image" src={option.image} alt={option.alt} loading="lazy" />
                </div>
              ))}
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
