/**
 * SamplingResultView - Vista de resultados del muestreo
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import DiagramasPalletView from './DiagramasPalletView';
import OcrImageUpload from './OcrImageUpload';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import './SamplingResultView.css';
import usdaLogo from '../images/usda.svg';
import chileLogoImg from '../images/logo_chile.png';
// Importar con alias para manejar espacio en el nombre
import minsalLogoImg from '../images/Logo MINSAL.jpg';

function SamplingResultView({ result, onNewInspection }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { inspection, sampling_result } = result;
  const [printingZebra, setPrintingZebra] = useState(false);
  const [zebraError, setZebraError] = useState(null);
  const [manualNumbersInput, setManualNumbersInput] = useState('');
  const [manualNumbers, setManualNumbers] = useState([]);
  const [editingNumber, setEditingNumber] = useState(null); // Controla qué número se está editando
  const [editValue, setEditValue] = useState(''); // Valor temporal mientras se edita
  const [showDiagrams, setShowDiagrams] = useState(false);
  const [labelSize, setLabelSize] = useState('standard'); // 'standard' (5x5) o 'small_5x2'
  const resolveSampleLabel = (userData) => {
    return (
      userData?.establishment?.sample_label_text ||
      userData?.sample_label_text ||
      userData?.profile?.sample_label_text ||
      'MUESTRA USDA'
    ).trim();
  };

  const labelText = resolveSampleLabel(user);

  // Debug: Log del usuario y labelText
  useEffect(() => {
    console.log('DEBUG - User object:', user);
    console.log('DEBUG - sample_label_text:', user?.sample_label_text);
    console.log('DEBUG - labelText:', labelText);
  }, [user, labelText]);

  // Parsear números ingresados en el textarea
  const parseManualNumbers = () => {
    // Eliminar duplicados y ordenar de menor a mayor
    return Array.from(new Set(manualNumbers)).sort((a, b) => a - b);
  };


  // Agregar número a la lista
  const addManualNumber = () => {
    const num = parseInt(manualNumbersInput.trim(), 10);
    if (isNaN(num) || num <= 0) {
      setZebraError('Ingresa un número válido (mayor a 0)');
      return;
    }
    
    if (manualNumbers.includes(num)) {
      setZebraError(`El número ${num} ya existe`);
      return;
    }

    setManualNumbers([...manualNumbers, num]);
    setManualNumbersInput('');
    setZebraError(null);
  };

  // Eliminar número de la lista
  const removeManualNumber = (num) => {
    setManualNumbers(manualNumbers.filter(n => n !== num));
  };

  // Iniciar edición de un número
  const startEditingNumber = (num) => {
    setEditingNumber(num);
    setEditValue(num.toString());
  };

  // Guardar cambio del número editado
  const saveEditedNumber = (oldNum) => {
    const parsed = parseInt(editValue.trim(), 10);
    
    if (isNaN(parsed) || parsed <= 0) {
      setZebraError('Ingresa un número válido (mayor a 0)');
      return;
    }
    
    if (parsed !== oldNum && manualNumbers.includes(parsed)) {
      setZebraError(`El número ${parsed} ya existe`);
      return;
    }

    // Actualizar solo el número que se estaba editando
    setManualNumbers(manualNumbers.map(n => n === oldNum ? parsed : n));
    setEditingNumber(null);
    setEditValue('');
    setZebraError(null);
  };

  // Cancelar edición
  const cancelEditingNumber = () => {
    setEditingNumber(null);
    setEditValue('');
  };

  // Handlers para el modal de diagramas
  const handleCloseDiagrams = () => {
    setShowDiagrams(false);
  };

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
    doc.text('AGROSAMPLE - Muestreo de Lote', pageWidth / 2, 15, { align: 'center' });
    doc.text(`Despacho: ${inspection.tipo_despacho || 'N/A'}`, pageWidth / 2, 20, { align: 'center' });
    
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
    
    doc.text('Inspector', leftCol, yPos);
    doc.text(': ' + (inspection.inspector_sag || ''), leftValCol, yPos);
    yPos += 6;
    
    doc.text('Responsable', leftCol, yPos);
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
    doc.text('Certificado de Muestreo', pageWidth / 2, yPos, { align: 'center' });
    yPos += 5;
    doc.text(`Detalle del Lote Nro    : ${inspection.numero_lote}`, pageWidth / 2, yPos, { align: 'center' });
    yPos += 10;
    
    // Campos del certificado
    doc.setFont('helvetica', 'normal');
    const certLeftCol = 25;
    
    doc.text(`${labelText} :`, certLeftCol, yPos);
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
    // Usar números del estado
    const parsedNumbers = parseManualNumbers();
    
    if (parsedNumbers.length === 0) {
      setZebraError('Ingresa al menos un número de caja válido');
      return;
    }

    setPrintingZebra(true);
    setZebraError(null);

    try {
      let effectiveLabelText = labelText;

      // Obtener etiqueta más reciente desde backend para evitar usar datos en caché.
      try {
        const latestUser = await apiService.getCurrentUser();
        const latestLabel = resolveSampleLabel(latestUser) || labelText;
        if (latestLabel) {
          effectiveLabelText = latestLabel;
        }
      } catch (refreshUserError) {
        console.warn('No se pudo refrescar usuario antes de imprimir, usando etiqueta de sesión.', refreshUserError);
      }

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

      // Enviar datos de impresión con los números parseados
      const response = await fetch(`${PRINT_SERVICE_URL}/print`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lote: inspection.numero_lote,
          numeros: parsedNumbers,
          printer: selectedPrinter,
          // Enviar múltiples alias para compatibilidad con distintas versiones del servicio.
          sample_text: effectiveLabelText,
          sample_label_text: effectiveLabelText,
          label_text: effectiveLabelText,
          leyenda: effectiveLabelText,
          label_size: labelSize,
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
      {/* Información de la Inspección — barra compacta */}
      <div className="inspection-info-bar">
        <div className="info-bar-brand">
          <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h7a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
          Inspección
        </div>
        <div className="info-bar-divider" />
        <div className="info-bar-item">
          <span className="info-bar-label">Lote</span>
          <span className="info-bar-value">{inspection.numero_lote}</span>
        </div>
        <div className="info-bar-divider" />
        <div className="info-bar-item">
          <span className="info-bar-label">Pallets</span>
          <span className="info-bar-value">{inspection.cantidad_pallets}</span>
        </div>
        <div className="info-bar-divider" />
        <div className="info-bar-item">
          <span className="info-bar-label">Fecha</span>
          <span className="info-bar-value">{new Date(inspection.fecha).toLocaleDateString('es-CL')}</span>
        </div>
        <div className="info-bar-divider" />
        <div className="info-bar-item">
          <span className="info-bar-label">Etiqueta</span>
          <span className="info-bar-value info-bar-badge">{labelText}</span>
        </div>
      </div>

      {/* Ingreso Manual de Números */}
      <div className="card result-card">
        <div className="card-header">
          <h2>Ingreso Manual de Números</h2>
          <p className="card-subtitle">Ingresa los números de cajas que serán capturados en el diagrama</p>
        </div>

        <div className="card-body">
          <div className="manual-input-section">
            <label htmlFor="manual-number-input" className="input-label">
              Ingreso de Números de Cajas
            </label>
            
            {/* Input + Agregar + Subir Imagen — mismo renglón */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
              <input
                id="manual-number-input"
                type="text"
                className="manual-input-textarea"
                style={{ flex: 1, minWidth: '120px', padding: '10px 12px' }}
                placeholder="Ej: 5 o 12 o 88"
                value={manualNumbersInput}
                inputMode="numeric"
                pattern="[0-9]*"
                autoComplete="off"
                onChange={(e) => {
                  const sanitized = e.target.value.replace(/\D/g, '');
                  setManualNumbersInput(sanitized);
                  setZebraError(null);
                }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addManualNumber();
                  }
                }}
              />
              <button
                className="btn btn-upload"
                onClick={addManualNumber}
                style={{ whiteSpace: 'nowrap' }}
              >
                + Agregar
              </button>
              <OcrImageUpload
                existingNumbers={manualNumbers}
                onConfirm={(merged) => {
                  setManualNumbers(merged);
                  setZebraError(null);
                }}
              />
            </div>

            <small style={{ color: '#4b5563', display: 'block', marginBottom: '12px' }}>
              Presiona Enter o click en "+ Agregar" · o sube una imagen con los números
            </small>


            {/* Lista de números ingresados */}
            {manualNumbers.length > 0 && (
              <div style={{
                display: 'grid',
                gap: '8px',
                padding: '12px',
                backgroundColor: '#f0fdf4',
                borderRadius: '8px',
                border: '1px solid #d1fae5',
                marginBottom: '12px'
              }}>
                <div style={{ fontSize: '0.9em', fontWeight: '600', color: '#059669', marginBottom: '4px' }}>
                  ✓ Números capturados ({manualNumbers.length}):
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {parseManualNumbers().map((num, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        backgroundColor: editingNumber === num ? '#0891b2' : '#10b981',
                        color: 'white',
                        borderRadius: '6px',
                        padding: '6px 10px',
                        fontSize: '0.95em',
                        fontWeight: '600',
                        transition: 'all 0.2s',
                      }}
                    >
                      {editingNumber === num ? (
                        // Modo edición
                        <>
                          <input
                            type="number"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                saveEditedNumber(num);
                              } else if (e.key === 'Escape') {
                                cancelEditingNumber();
                              }
                            }}
                            autoFocus
                            style={{
                              width: '50px',
                              padding: '4px 6px',
                              border: '2px solid rgba(255,255,255,0.5)',
                              borderRadius: '4px',
                              fontSize: '0.95em',
                              backgroundColor: 'rgba(0,0,0,0.2)',
                              color: 'white',
                              textAlign: 'center',
                            }}
                            onClick={(e) => e.stopPropagation()}
                          />
                          <button
                            onClick={() => saveEditedNumber(num)}
                            style={{
                              background: 'rgba(255,255,255,0.4)',
                              border: 'none',
                              color: 'white',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              padding: '2px 6px',
                              fontSize: '0.85em',
                              transition: 'all 0.2s',
                            }}
                            onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.6)'}
                            onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.4)'}
                            title="Guardar (Enter)"
                          >
                            ✓
                          </button>
                          <button
                            onClick={cancelEditingNumber}
                            style={{
                              background: 'rgba(255,255,255,0.4)',
                              border: 'none',
                              color: 'white',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              padding: '2px 6px',
                              fontSize: '0.85em',
                              transition: 'all 0.2s',
                            }}
                            onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.6)'}
                            onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.4)'}
                            title="Cancelar (Esc)"
                          >
                            ✕
                          </button>
                        </>
                      ) : (
                        // Modo lectura
                        <>
                          <span
                            onClick={() => startEditingNumber(num)}
                            style={{
                              cursor: 'pointer',
                              padding: '2px 4px',
                              borderRadius: '3px',
                              transition: 'all 0.2s',
                            }}
                            onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(0,0,0,0.2)'}
                            onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                            title="Click para editar"
                          >
                            {num}
                          </span>
                          <button
                            onClick={() => removeManualNumber(num)}
                            style={{
                              background: 'rgba(255,255,255,0.3)',
                              border: 'none',
                              color: 'white',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              padding: '2px 6px',
                              fontSize: '0.85em',
                              transition: 'all 0.2s',
                            }}
                            onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.5)'}
                            onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.3)'}
                            title="Eliminar"
                          >
                            ✕
                          </button>
                        </>
                      )}
                    </div>
                  ))}
                </div>
                <small style={{ color: '#059669', marginTop: '4px' }}>
                  Haz click en el número para editar (Enter para guardar, Esc para cancelar)
                </small>
              </div>
            )}
          </div>

          {/* Error de Zebra */}
          {zebraError && (
            <div style={{
              padding: '12px',
              marginBottom: '16px',
              backgroundColor: '#fee2e2',
              color: '#991b1b',
              borderRadius: '8px',
              border: '1px solid #fecaca',
              fontSize: '0.95em'
            }}>
              ⚠️ {zebraError}
            </div>
          )}

          {/* Selector de tamaño de adhesivo */}
          <div style={{
            padding: '12px 0 6px',
            borderTop: '1px solid #e5e7eb',
            marginBottom: '4px',
          }}>
            <div style={{ fontSize: '0.85rem', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
              🏷️ Tamaño del adhesivo:
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                onClick={() => setLabelSize('standard')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 14px',
                  borderRadius: '8px',
                  border: labelSize === 'standard' ? '2px solid #10b981' : '2px solid #d1d5db',
                  background: labelSize === 'standard' ? '#f0fdf4' : '#fff',
                  color: labelSize === 'standard' ? '#065f46' : '#6b7280',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {labelSize === 'standard' && <span>✓</span>}
                Estándar (5×5 cm) — doble
              </button>
              <button
                onClick={() => setLabelSize('small_5x2')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 14px',
                  borderRadius: '8px',
                  border: labelSize === 'small_5x2' ? '2px solid #10b981' : '2px solid #d1d5db',
                  background: labelSize === 'small_5x2' ? '#f0fdf4' : '#fff',
                  color: labelSize === 'small_5x2' ? '#065f46' : '#6b7280',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {labelSize === 'small_5x2' && <span>✓</span>}
                Pequeño (5×2 cm) — doble
              </button>
            </div>
          </div>

          {/* Acciones */}
          <div className="actions-section">
            <button 
              className="btn btn-upload"
              onClick={printZebraLabels}
              disabled={printingZebra}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5 4v3H4a2 2 0 00-2 2v3a2 2 0 002 2h1v2a2 2 0 002 2h6a2 2 0 002-2v-2h1a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z" clipRule="evenodd" />
              </svg>
              {printingZebra ? 'Imprimiendo...' : 'Etiquetas Zebra'}
            </button>

            <button 
              className="btn btn-upload"
              onClick={() => setShowDiagrams(true)}
              title="Configurar y ver diagramas de pallets"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
              Diagrama Pallets
            </button>

            <button 
              className="btn btn-upload"
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

      {/* Modal de Configuración de Diagramas */}
      {showDiagrams && (
        <DiagramasPalletView
          inspection={inspection}
          selectedNumbers={parseManualNumbers()}
          onClose={handleCloseDiagrams}
        />
      )}
    </div>
  );
}

export default SamplingResultView;
