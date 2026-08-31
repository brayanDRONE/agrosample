/**
 * DispatchFlatFileApp - Pantalla base para el futuro módulo de plano de despacho.
 */

import { ThemeProvider } from '../contexts/ThemeContext';
import Header from './Header';
import './DispatchFlatFileApp.css';

function DispatchFlatFileAppContent() {
  return (
    <div className="app dispatch-app">
      <Header />

      <main className="main-container">
        <div className="content-wrapper">
          <section className="dispatch-shell">
            <div className="dispatch-hero">
              <h1>Generar Plano de Despacho</h1>
              <p>
                Espacio reservado para el futuro flujo de despacho.
              </p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

function DispatchFlatFileApp() {
  return (
    <ThemeProvider>
      <DispatchFlatFileAppContent />
    </ThemeProvider>
  );
}

export default DispatchFlatFileApp;