/**
 * SamplingResultView - Vista de resultados del muestreo
 */

import { useState, useEffect } from 'react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import DiagramasPalletView from './DiagramasPalletView';
import './SamplingResultView.css';
import usdaLogo from '../images/usda.svg';
import chileLogoImg from '../images/logo_chile.png';
// Importar con alias para manejar espacio en el nombre
import minsalLogoImg from '../images/Logo MINSAL.jpg';

function SamplingResultView({ result, onNewInspection }) {
  const { inspection, sampling_result } = result;
  const [printingZebra, setPrintingZebra] = useState(false);
  const [zebraError, setZebraError] = useState(null);
  const [showDiagrams, setShowDiagrams] = useState(false);

  const generatePDF = async () => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.width;
    
    // ==================== HEADER SECTION - LOGOS ====================
    // Función auxiliar para cargar imagen
    const loadImage = (src) => {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = src;
      });
    };

    try {
      // Cargar y agregar Logo USDA (superior izquierda)
      // Para SVG, lo cargamos como imagen
      const usdaImg = await loadImage(usdaLogo);
      const canvas1 = document.createElement('canvas');
      canvas1.width = 150;
      canvas1.height = 90;
      const ctx1 = canvas1.getContext('2d');
      ctx1.drawImage(usdaImg, 0, 0, 150, 90);
      const usdaData = canvas1.toDataURL('image/png');
      doc.addImage(usdaData, 'PNG', 10, 8, 30, 18);
      
      // Logo Chile (superior derecha)
      doc.addImage(chileLogoImg, 'PNG', pageWidth - 45, 8, 35, 20);
      
      // Logo MINSAL (debajo del logo Chile)
      doc.addImage(minsalLogoImg, 'JPEG', pageWidth - 45, 30, 35, 15);
    } catch (error) {
      console.warn('Error al cargar logos:', error);
      // Continuar sin logos si hay error
    }
    
    // Título centrado
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text('Muestreo Aleatorio con Despacho', pageWidth / 2, 15, { align: 'center' });
    doc.text(`a ${inspection.tipo_despacho}`, pageWidth / 2, 20, { align: 'center' });
    
    // ==================== NRO LOTE Y PRODUCTO (HORIZONTAL CENTRADO) ====================
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    
    // Posición inicial después de los logos (MINSAL termina en Y=45)
    let yPos = 50;
    
    // COLUMNA IZQUIERDA
    const leftCol = 15;
    const leftValCol = 60;
    
    // COLUMNA DERECHA
    const rightCol = 110;
    const rightValCol = 160;
    
    // Nro. de Lote (alineado con columna izquierda) y Producto (alineado con columna derecha)
    doc.text(`Nro. de Lote : ${inspection.numero_lote || ''}`, leftCol, yPos);
    doc.text(`Producto : ${inspection.especie || ''}`, rightCol, yPos);
    
    // ==================== SECCIÓN DE DATOS EN DOS COLUMNAS ====================
    yPos = 58; // Iniciar las columnas más abajo
    
    doc.text('Exportador', leftCol, yPos);
    doc.text(': ' + (inspection.exportador || ''), leftValCol, yPos);
    yPos += 6;
    
    doc.text('Fecha', leftCol, yPos);
    const fecha = new Date(inspection.fecha);
    doc.text(`: ${fecha.toLocaleDateString('es-CL')}`, leftValCol, yPos);
    yPos += 6;
    
    doc.text('Inspector SAG', leftCol, yPos);
    doc.text(': ' + (inspection.inspector_sag || ''), leftValCol, yPos);
    yPos += 6;
    
    doc.text('Responsable Planta', leftCol, yPos);
    doc.text(': ' + (inspection.contraparte_sag || ''), leftValCol, yPos);
    yPos += 6;
    
    doc.text('Tamaño de la Partida', leftCol, yPos);
    doc.text(': ' + (inspection.tamano_lote || ''), leftValCol, yPos);
    yPos += 6;
    
    doc.text('Tipo de Muestreo', leftCol, yPos);
    doc.text(': ' + (inspection.tipo_muestreo === 'NORMAL' ? 'Normal' : 'Por Etapa'), leftValCol, yPos);
    yPos += 6;
    
    // Para muestreo por etapa, mostrar pallets seleccionados
    if (inspection.tipo_muestreo === 'POR_ETAPA' && result.stage_sampling) {
      doc.text('Pallets Seleccionados', leftCol, yPos);
      const selectedPalletsText = result.stage_sampling.selected_pallets.map(p => p + 1).join(', ');
      doc.text(`: ${selectedPalletsText}`, leftValCol, yPos);
      yPos += 6;
    } else {
      doc.text('Pallets a Muestrear', leftCol, yPos);
      doc.text(': (No zanja).', leftValCol, yPos);
      yPos += 6;
    }
    
    // COLUMNA DERECHA
    yPos = 58; // Reset a la misma altura que columna izquierda
    
    doc.text('Planta', rightCol, yPos);
    doc.text(': ' + (inspection.establecimiento_nombre || inspection.establishment_name || ''), rightValCol, yPos);
    yPos += 6;
    
    doc.text('Hora', rightCol, yPos);
    // Formatear hora para mostrar solo HH:MM:SS sin microsegundos
    const horaFormateada = inspection.hora ? inspection.hora.split('.')[0] : '';
    doc.text(': ' + horaFormateada, rightValCol, yPos);
    yPos += 6;
    
    // Espacio (saltar responsable planta de la derecha)
    yPos += 6;
    
    doc.text(`Tabla de Muestreo: ${sampling_result.nombre_tabla || 'Hipergeométrica del 6%'}`, rightCol, yPos);
    yPos += 6;
    
    doc.text('Tamaño de la Muestra', rightCol, yPos);
    doc.text(': ' + (sampling_result.tamano_muestra || ''), rightValCol, yPos);
    yPos += 6;
    
    doc.text('Nro. de Pallets', rightCol, yPos);
    doc.text(': ' + (inspection.cantidad_pallets || ''), rightValCol, yPos);
    
    // ==================== TABLA DE NÚMEROS DE CAJAS MUESTRA ====================
    yPos = 104; // Ajustado para el nuevo espaciado
    doc.setFont('helvetica', 'bold');
    doc.text('Números de Cajas Muestra:', pageWidth / 2, yPos, { align: 'center' });
    
    // Preparar datos para tabla de 10 columnas
    const cajas = sampling_result.cajas_seleccionadas;
    const itemsPerRow = 10;
    const cajasData = [];
    
    for (let i = 0; i < cajas.length; i += itemsPerRow) {
      const row = cajas.slice(i, i + itemsPerRow);
      // Rellenar con vacíos si la fila no está completa
      while (row.length < itemsPerRow) {
        row.push('');
      }
      cajasData.push(row);
    }
    
    // Generar tabla con autoTable (sin encabezados)
    // Crear columnStyles dinámicamente para 10 columnas
    const columnStyles = {};
    for (let i = 0; i < 10; i++) {
      columnStyles[i] = { cellWidth: 18 }; // Columnas más estrechas para caber 10
    }
    
    autoTable(doc, {
      startY: yPos + 5,
      body: cajasData,
      theme: 'grid',
      styles: {
        fontSize: 10,
        cellPadding: 2,
        halign: 'center',
        lineWidth: 0.1,
        lineColor: [0, 0, 0],
      },
      margin: { left: 10, right: 10 },
      tableWidth: 'auto',
      columnStyles: columnStyles,
    });
    
    // ==================== CERTIFICADO DE PRE-MUESTREO ====================
    // Posicionar siempre al final de la página (independiente de la cantidad de números)
    const pageHeight = doc.internal.pageSize.height;
    const certificateHeight = 65; // Altura aproximada del certificado
    yPos = pageHeight - certificateHeight - 15; // 15mm de margen inferior
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.text('Certificado de Pre-Muestreo USDA/SAG', pageWidth / 2, yPos, { align: 'center' });
    yPos += 5;
    doc.text(`Detalle del Lote Nro    : ${inspection.numero_lote}`, pageWidth / 2, yPos, { align: 'center' });
    yPos += 10;
    
    // Campos del certificado
    doc.setFont('helvetica', 'normal');
    const certLeftCol = 25;
    
    doc.text('MUESTRA   :', certLeftCol, yPos);
    doc.text('DE', certLeftCol + 30, yPos);
    doc.rect(certLeftCol + 40, yPos - 4, 40, 6); // Campo vacío
    doc.text('A', certLeftCol + 85, yPos);
    doc.rect(certLeftCol + 92, yPos - 4, 40, 6); // Campo vacío
    yPos += 10;
    
    doc.text('LOTE           :', certLeftCol, yPos);
    doc.text('DE', certLeftCol + 30, yPos);
    doc.rect(certLeftCol + 40, yPos - 4, 40, 6); // Campo vacío
    doc.text('A', certLeftCol + 85, yPos);
    doc.rect(certLeftCol + 92, yPos - 4, 40, 6); // Campo vacío
    yPos += 10;
    
    doc.text('                     ', certLeftCol, yPos);
    doc.text('DE', certLeftCol + 30, yPos);
    doc.rect(certLeftCol + 40, yPos - 4, 40, 6); // Campo vacío
    doc.text('A', certLeftCol + 85, yPos);
    doc.rect(certLeftCol + 92, yPos - 4, 40, 6); // Campo vacío
    yPos += 10;
    
    doc.text('Remanentes   :', certLeftCol, yPos);
    doc.rect(certLeftCol + 40, yPos - 4, 40, 6); // Campo vacío
    doc.text('Cajas', certLeftCol + 85, yPos);
    
    // ==================== NOTA AL PIE ====================
    yPos = doc.internal.pageSize.height - 15;
    doc.setFontSize(8);
    doc.setFont('helvetica', 'italic');
    doc.text('Señor Inspector: Verifique los Números del Listado con los de las Cajas Muestras.', 
             pageWidth / 2, yPos, { align: 'center' });
    
    // Guardar PDF
    const fileName = `Muestreo_${inspection.numero_lote}_${fecha.toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
  };

  const printZebraLabels = async () => {
    setPrintingZebra(true);
    setZebraError(null);

    try {
      // Verificar que el servicio esté disponible y obtener impresoras
      const PRINT_SERVICE_URL = import.meta.env.VITE_PRINT_SERVICE_URL || 'http://localhost:5000';
      const healthResponse = await fetch(`${PRINT_SERVICE_URL}/health`);
      if (!healthResponse.ok) {
        throw new Error('Servicio de impresión no disponible');
      }

      const healthData = await healthResponse.json();
      // Retrocompatibilidad: aceptar tanto 'printers' como 'printers_available'
      const printers = healthData.printers || healthData.printers_available || [];

      if (printers.length === 0) {
        throw new Error('No se detectaron impresoras en el sistema');
      }

      // Mostrar diálogo para seleccionar impresora
      let printerOptions = printers.map((p, i) => `${i + 1}. ${p}`).join('\n');
      
      // Buscar impresora Zebra por defecto
      let defaultIndex = printers.findIndex(p => 
        p.toLowerCase().includes('zebra') || p.toLowerCase().includes('zdesigner')
      );
      
      if (defaultIndex === -1) defaultIndex = 0;
      
      const mensaje = `Seleccione la impresora:\n\n${printerOptions}\n\n` +
        `Ingrese el número (por defecto: ${defaultIndex + 1} - ${printers[defaultIndex]})`;
      
      const seleccion = prompt(mensaje, (defaultIndex + 1).toString());
      
      if (seleccion === null) {
        // Usuario canceló
        setPrintingZebra(false);
        return;
      }
      
      const printerIndex = parseInt(seleccion) - 1;
      if (isNaN(printerIndex) || printerIndex < 0 || printerIndex >= printers.length) {
        throw new Error('Selección de impresora inválida');
      }
      
      const selectedPrinter = printers[printerIndex];

      // Enviar datos de impresión
      const response = await fetch(`${PRINT_SERVICE_URL}/print`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lote: inspection.numero_lote,
          numeros: sampling_result.cajas_seleccionadas,
          printer: selectedPrinter
        }),
      });

      const result = await response.json();

      if (result.success) {
        alert(result.message);
      } else {
        throw new Error(result.error || 'Error desconocido al imprimir');
      }
    } catch (error) {
      const errorMsg = error.message.includes('Failed to fetch') 
        ? 'No se pudo conectar al servicio de impresión.\n\nAsegúrese de que:\n1. El servicio zebra_print_service.py esté ejecutándose\n2. Esté corriendo en http://localhost:5000\n3. La impresora Zebra esté conectada'
        : error.message;
      
      setZebraError(errorMsg);
      alert('❌ Error de impresión:\n\n' + errorMsg);
    } finally {
      setPrintingZebra(false);
    }
  };

  return (
    <div className="results-container">
      {/* Información de la Inspección */}
      <div className="card result-card">
        <div className="card-header success-header">
          <div className="success-icon">
            <svg width="32" height="32" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h2>Muestreo Generado Exitosamente</h2>
            <p>Lote: {inspection.numero_lote} - {inspection.especie}</p>
          </div>
        </div>

        {/* Detalles de Inspección */}
        <div className="card-body">
          <div className="info-section">
            <h3 className="section-title">Información de la Inspección</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Exportador:</span>
                <span className="info-value">{inspection.exportador}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Establecimiento:</span>
                <span className="info-value">{inspection.establecimiento_nombre || inspection.establishment_name}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Inspector SAG:</span>
                <span className="info-value">{inspection.inspector_sag}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Contraparte SAG:</span>
                <span className="info-value">{inspection.contraparte_sag}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Fecha:</span>
                <span className="info-value">
                  {new Date(inspection.fecha).toLocaleDateString('es-CL')}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Tipo de Muestreo:</span>
                <span className="info-value">
                  {inspection.tipo_muestreo === 'NORMAL' ? 'Normal' : 'Por Etapa'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Tipo de Despacho:</span>
                <span className="info-value">{inspection.tipo_despacho}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Cantidad de Pallets:</span>
                <span className="info-value">{inspection.cantidad_pallets}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Resultados del Muestreo */}
      <div className="card result-card">
        <div className="card-header">
          <h2>Resultados del Muestreo</h2>
        </div>

        <div className="card-body">
          {/* Estadísticas */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Tamaño del Lote</div>
              <div className="stat-value">{sampling_result.tamano_lote}</div>
              <div className="stat-unit">cajas</div>
            </div>

            <div className="stat-card stat-highlight">
              <div className="stat-label" style={{ fontSize: '0.9em' }}>Tabla de Muestreo</div>
              <div className="stat-value" style={{ fontSize: '0.8em', lineHeight: '1.2', padding: '5px' }}>
                {sampling_result.nombre_tabla || 'Hipergeométrica del 6%'}
              </div>
              <div className="stat-unit" style={{ fontSize: '0.85em' }}>aplicada</div>
            </div>

            <div className="stat-card stat-primary">
              <div className="stat-label">Tamaño de la Muestra</div>
              <div className="stat-value">{sampling_result.tamano_muestra}</div>
              <div className="stat-unit">cajas a inspeccionar</div>
              {sampling_result.incremento_aplicado > 0 && (
                <div style={{ marginTop: '8px', fontSize: '0.85em', color: '#059669', fontWeight: 600 }}>
                  Base: {sampling_result.muestra_base} → Final: {sampling_result.muestra_final}
                </div>
              )}
            </div>
          </div>

          {/* Información adicional para Muestreo por Etapa */}
          {inspection.tipo_muestreo === 'POR_ETAPA' && result.stage_sampling && (
            <div className="stage-sampling-info">
              <div className="info-box info-box-primary">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div>
                  <strong>Muestreo por Etapa:</strong> Se seleccionaron {result.stage_sampling.selected_pallets.length} pallets 
                  ({Math.round((result.stage_sampling.selected_pallets.length / inspection.cantidad_pallets) * 100)}% del total)
                  <div style={{ marginTop: '8px' }}>
                    <strong>Pallets Seleccionados:</strong> {result.stage_sampling.selected_pallets.join(', ')}
                  </div>
                  {sampling_result.tamano_lote_muestreado && (
                    <div style={{ marginTop: '4px', fontSize: '0.95em', color: '#059669', fontWeight: 600 }}>
                      Cajas en pallets seleccionados: {sampling_result.tamano_lote_muestreado} 
                      (de {sampling_result.tamano_lote} totales)
                    </div>
                  )}
                  <div style={{ marginTop: '4px', fontSize: '0.9em', opacity: '0.9' }}>
                    Total de pallets en el lote: {inspection.cantidad_pallets}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Lista de Cajas */}
          <div className="boxes-section">
            <h3 className="section-title">
              Cajas Seleccionadas ({sampling_result.cajas_seleccionadas.length})
            </h3>
            <div className="boxes-container">
              {sampling_result.cajas_seleccionadas.map((numero, index) => (
                <div key={index} className="box-number">
                  {numero}
                </div>
              ))}
            </div>
          </div>

          {/* Acciones */}
          <div className="actions-section">
            <button 
              className="btn btn-success"
              onClick={generatePDF}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clipRule="evenodd" />
              </svg>
              Imprimir PDF
            </button>

            <button 
              className="btn btn-secondary"
              onClick={printZebraLabels}
              disabled={printingZebra}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5 4v3H4a2 2 0 00-2 2v3a2 2 0 002 2h1v2a2 2 0 002 2h6a2 2 0 002-2v-2h1a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z" clipRule="evenodd" />
              </svg>
              {printingZebra ? 'Imprimiendo...' : 'Etiquetas Zebra'}
            </button>

            <button 
              className="btn btn-secondary"
              onClick={() => setShowDiagrams(true)}
              title="Configurar y ver diagramas de pallets"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
              Diagrama Pallets
            </button>

            <button 
              className="btn btn-primary"
              onClick={onNewInspection}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
              </svg>
              Nueva Inspección
            </button>
          </div>
        </div>
      </div>

      {/* Modal de diagramas */}
      {showDiagrams && (
        <DiagramasPalletView
          inspection={inspection}
          onClose={() => setShowDiagrams(false)}
        />
      )}
    </div>
  );
}

export default SamplingResultView;
