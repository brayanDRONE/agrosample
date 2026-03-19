/**
 * ConfiguracionDiagramaView - Vista para configurar base y altura de cada pallet
 * 
 * Permite al usuario ingresar configuración individual para cada pallet
 * antes de generar los diagramas.
 */

import { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { jsPDF } from 'jspdf';
import { useAuth } from '../contexts/AuthContext';
import './ConfiguracionDiagramaView.css';

function ConfiguracionDiagramaView({ inspection: inspectionProp, onConfigured, onClose }) {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { inspectionId } = useParams();
  
  // Obtener inspection del state de navigation o de props (mode modal vs página)
  const inspection = location.state?.inspection || inspectionProp;
  const [configurations, setConfigurations] = useState([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);


  useEffect(() => {
    initializeConfigurations();
  }, [inspection]);

  /**
   * Obtiene la distribución de caras sugerida según la base
   */
  const getDefaultDistribucion = (base) => {
    const baseNum = parseInt(base);
    if (isNaN(baseNum) || baseNum < 1) return [];

    // Templates predefinidos
    switch (baseNum) {
      case 5:
        return [2, 3]; // Cara A: 2 cols, Cara B: 3 cols
      case 6:
        return [3, 3]; // Cara A: 3 cols, Cara B: 3 cols
      case 8:
        return [4, 4]; // Cara A: 4 cols, Cara B: 4 cols
      case 10:
        return [5, 5]; // Cara A: 5 cols, Cara B: 5 cols
      default:
        // Para otras bases, intentar dividir en 2 caras iguales
        if (baseNum % 2 === 0) {
          return [baseNum / 2, baseNum / 2];
        }
        // Si es impar, dividir lo más equitativo posible
        return [Math.floor(baseNum / 2), Math.ceil(baseNum / 2)];
    }
  };

  const initializeConfigurations = () => {
    // Determinar qué pallets configurar
    let palletsToConfig = [];
    
    if (inspection.tipo_muestreo === 'POR_ETAPA') {
      // Solo pallets seleccionados
      palletsToConfig = inspection.selected_pallets || [];
    } else {
      // Todos los pallets
      palletsToConfig = Array.from({ length: inspection.cantidad_pallets }, (_, i) => i + 1);
    }

    // Inicializar con valores vacíos o existentes
    const existingConfigs = inspection.pallet_configurations || [];
    const configMap = {};
    existingConfigs.forEach(c => {
      configMap[c.numero_pallet] = c;
    });

    // Obtener boxes_per_pallet para valores por defecto
    const boxesPerPallet = inspection.boxes_per_pallet || [];

    const configs = palletsToConfig.map(numPallet => {
      if (configMap[numPallet]) {
        // Si ya existe configuración, asegurarse de que tenga distribucion_caras
        return {
          ...configMap[numPallet],
          distribucion_caras: configMap[numPallet].distribucion_caras || getDefaultDistribucion(configMap[numPallet].base),
          distribucion_personalizada: configMap[numPallet].distribucion_personalizada || false
        };
      }
      
      // Si existe boxes_per_pallet, usar ese valor como cantidad_cajas por defecto
      const cantidadCajasDefault = boxesPerPallet[numPallet - 1] || '';
      
      return {
        numero_pallet: numPallet,
        base: '',
        cantidad_cajas: cantidadCajasDefault,
        distribucion_caras: [],
        distribucion_personalizada: false
      };
    });

    setConfigurations(configs);
  };

  const handleConfigChange = (index, field, value) => {
    const newConfigs = [...configurations];
    newConfigs[index][field] = value;
    
    // Si cambia la base y no está en modo personalizado, actualizar distribucion_caras
    if (field === 'base' && !newConfigs[index].distribucion_personalizada) {
      newConfigs[index].distribucion_caras = getDefaultDistribucion(value);
    }
    
    setConfigurations(newConfigs);
    setError(null);
  };

  const handleDistribucionChange = (index, caraIndex, value) => {
    const newConfigs = [...configurations];
    const newDistribucion = [...(newConfigs[index].distribucion_caras || [])];
    newDistribucion[caraIndex] = parseInt(value) || 0;
    newConfigs[index].distribucion_caras = newDistribucion;
    newConfigs[index].distribucion_personalizada = true;
    setConfigurations(newConfigs);
    setError(null);
  };

  const togglePersonalizado = (index) => {
    const newConfigs = [...configurations];
    const config = newConfigs[index];
    
    if (config.distribucion_personalizada) {
      // Volver al template predefinido
      config.distribucion_personalizada = false;
      config.distribucion_caras = getDefaultDistribucion(config.base);
    } else {
      // Activar modo personalizado
      config.distribucion_personalizada = true;
    }
    
    setConfigurations(newConfigs);
  };

  const agregarCara = (index) => {
    const newConfigs = [...configurations];
    const distribucion = newConfigs[index].distribucion_caras || [];
    newConfigs[index].distribucion_caras = [...distribucion, 1];
    newConfigs[index].distribucion_personalizada = true;
    setConfigurations(newConfigs);
  };

  const eliminarCara = (index, caraIndex) => {
    const newConfigs = [...configurations];
    const newDistribucion = [...(newConfigs[index].distribucion_caras || [])];
    newDistribucion.splice(caraIndex, 1);
    newConfigs[index].distribucion_caras = newDistribucion;
    setConfigurations(newConfigs);
  };

  const applyToAll = () => {
    const firstConfig = configurations[0];
    if (!firstConfig.base || !firstConfig.cantidad_cajas) {
      setError('Ingrese base y cantidad de cajas en el primer pallet para aplicar a todos');
      return;
    }

    const newConfigs = configurations.map(config => ({
      ...config,
      base: firstConfig.base,
      cantidad_cajas: firstConfig.cantidad_cajas
    }));

    setConfigurations(newConfigs);
  };

  const applyDistribucionToAll = () => {
    const firstConfig = configurations[0];
    if (!firstConfig.base || firstConfig.distribucion_caras.length === 0) {
      setError('Ingrese la base y configure la distribución de caras del primer pallet');
      return;
    }

    const newConfigs = configurations.map(config => ({
      ...config,
      distribucion_caras: [...firstConfig.distribucion_caras],
      distribucion_personalizada: firstConfig.distribucion_personalizada
    }));

    setConfigurations(newConfigs);
    setError(null);
  };

  const validateConfigurations = () => {
    for (const config of configurations) {
      if (!config.base || !config.cantidad_cajas) {
        return 'Debe ingresar base y cantidad de cajas para todos los pallets';
      }
      if (parseInt(config.base) < 1 || parseInt(config.cantidad_cajas) < 1) {
        return 'Base y cantidad de cajas deben ser mayores a 0';
      }
      
      // Validar distribución de caras
      const distribucion = config.distribucion_caras || [];
      if (distribucion.length === 0) {
        return `Debe definir la distribución de caras para el pallet ${config.numero_pallet}`;
      }
      
      const sumaCaras = distribucion.reduce((sum, cols) => sum + (parseInt(cols) || 0), 0);
      if (sumaCaras !== parseInt(config.base)) {
        return `La suma de columnas en las caras (${sumaCaras}) debe coincidir con la base (${config.base}) en el pallet ${config.numero_pallet}`;
      }
    }
    return null;
  };

  const handleSave = async () => {
    const validationError = validateConfigurations();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const payload = {
        configurations: configurations.map(c => ({
          numero_pallet: c.numero_pallet,
          base: parseInt(c.base),
          cantidad_cajas: parseInt(c.cantidad_cajas),
          distribucion_caras: c.distribucion_caras || getDefaultDistribucion(c.base)
        }))
      };

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      
      const headers = {
        'Content-Type': 'application/json'
      };
      
      // Solo agregar Authorization si existe token
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(
        `${API_URL}/muestreo/configurar-pallets/${inspection.id}/`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify(payload)
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Error al guardar configuraciones');
      }

      if (!data.success) {
        throw new Error(data.message);
      }

      // Notificar éxito
      if (inspectionId) {
        // Modo página independiente: mostrar mensaje después de 2 segundos
        setTimeout(() => {
          navigate('/muestreo');
        }, 2000);
      } else if (onConfigured) {
        // Modo modal: llamar callback después de 2 segundos
        setTimeout(() => {
          onConfigured();
        }, 2000);
      }
    } catch (err) {
      console.error('Error saving configurations:', err);
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const generateConfigPDF = () => {
    try {
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.width;
      const pageHeight = doc.internal.pageSize.height;
      let yPos = 20;
      const margin = 15;
      const footerHeight = 10;

      // Título
      doc.setFontSize(16);
      doc.setFont(undefined, 'bold');
      doc.text('Configuración de Diagramas de Pallets', pageWidth / 2, yPos, { align: 'center' });
      yPos += 15;

      // Información de la inspección
      doc.setFontSize(11);
      doc.setFont(undefined, 'bold');
      doc.text('Información de la Inspección', margin, yPos);
      yPos += 8;
      
      doc.setFontSize(10);
      doc.setFont(undefined, 'normal');
      doc.text(`Lote: ${inspection.numero_lote}`, margin, yPos);
      yPos += 6;
      doc.text(`Total de Pallets: ${configurations.length}`, margin, yPos);
      yPos += 6;
      doc.text(`Fecha: ${new Date().toLocaleDateString('es-CL')}`, margin, yPos);
      yPos += 12;

      // Tabla con configuraciones
      doc.setFontSize(11);
      doc.setFont(undefined, 'bold');
      doc.text('Detalle de Configuración por Pallet', margin, yPos);
      yPos += 10;

      // Headers de la tabla
      doc.setFontSize(9);
      doc.setFont(undefined, 'bold');
      const colWidths = [30, 30, 35, 50];
      const headers = ['Pallet', 'Base', 'Cantidad', 'Distribución Caras'];
      let xPos = margin;
      
      headers.forEach((header, idx) => {
        doc.text(header, xPos, yPos);
        xPos += colWidths[idx];
      });
      
      yPos += 8;
      doc.setDrawColor(200, 200, 200);
      doc.line(margin, yPos - 2, pageWidth - margin, yPos - 2);
      yPos += 5;

      // Datos de configuración
      doc.setFont(undefined, 'normal');
      configurations.forEach((config, idx) => {
        const distribucion = (config.distribucion_caras || []);
        const distribucionText = distribucion.map((col, i) => `Cara ${String.fromCharCode(65 + i)}: ${col}`).join(' | ');
        
        // Verificar si necesitamos nueva página
        if (yPos > pageHeight - footerHeight - 15) {
          // Pie de página
          doc.setFontSize(8);
          doc.setFont(undefined, 'normal');
          doc.text(`Página ${doc.internal.pages.length - 1}`, pageWidth / 2, pageHeight - 5, { align: 'center' });
          
          // Nueva página
          doc.addPage();
          yPos = 20;
          
          // Repetir headers en nueva página
          doc.setFontSize(9);
          doc.setFont(undefined, 'bold');
          xPos = margin;
          headers.forEach((header, idx) => {
            doc.text(header, xPos, yPos);
            xPos += colWidths[idx];
          });
          yPos += 8;
          doc.setDrawColor(200, 200, 200);
          doc.line(margin, yPos - 2, pageWidth - margin, yPos - 2);
          yPos += 5;
          doc.setFont(undefined, 'normal');
        }
        
        xPos = margin;
        doc.text(`Pallet ${config.numero_pallet}`, xPos, yPos);
        xPos += colWidths[0];
        
        doc.text(String(config.base), xPos, yPos);
        xPos += colWidths[1];
        
        doc.text(String(config.cantidad_cajas), xPos, yPos);
        xPos += colWidths[2];
        
        // Texto de distribución con wrapping
        const splitDistribucion = doc.splitTextToSize(distribucionText, colWidths[3] - 3);
        doc.text(splitDistribucion, xPos, yPos);
        
        yPos += Math.max(6, splitDistribucion.length * 4) + 3;
      });

      // Pie de página
      doc.setFontSize(8);
      doc.setFont(undefined, 'normal');
      doc.text(`Página ${doc.internal.pages.length - 1}`, pageWidth / 2, pageHeight - 5, { align: 'center' });

      // Descargar
      const filename = `Configuracion_Diagramas_${inspection.numero_lote}_${new Date().toISOString().split('T')[0]}.pdf`;
      doc.save(filename);
    } catch (err) {
      console.error('Error generating PDF:', err);
      alert('Error al generar el PDF');
    }
  };

  const getTotalCajas = () => {
    return configurations.reduce((sum, config) => {
      const cantidad = parseInt(config.cantidad_cajas) || 0;
      return sum + cantidad;
    }, 0);
  };

  // Handler para cerrar (adapta según contexto: modal vs página)
  const handleClose = () => {
    if (inspectionId) {
      // Modo página independiente
      navigate('/muestreo');
    } else if (onClose) {
      // Modo modal
      onClose();
    }
  };

  // Mostrar error si falta inspection data
  if (!inspection) {
    return (
      <div className="configuracion-overlay">
        <div className="configuracion-modal">
          <div className="configuracion-header">
            <h2>Error: Datos de inspección no disponibles</h2>
          </div>
          <div className="configuracion-info">
            <div className="info-alert" style={{ background: '#fee2e2', color: '#991b1b', borderRadius: '8px', padding: '12px' }}>
              No se pudo cargar la inspección. Por favor, intente nuevamente desde el formulario de ingreso.
            </div>
          </div>
          <div className="configuracion-footer">
            <button className="btn btn-secondary" onClick={handleClose}>
              Volver
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="configuracion-overlay">
      <div className="configuracion-modal">
        {/* Header */}
        <div className="configuracion-header">
          <div>
            <h2>Configuración de Diagramas de Pallets</h2>
            <p className="configuracion-subtitle">
              Ingrese base (cajas por capa) y cantidad total de cajas por pallet
            </p>
          </div>
          <button className="btn-close" onClick={handleClose}>
            {inspectionId ? '←' : '×'}
          </button>
        </div>

        {/* Info del lote */}
        <div className="configuracion-info">
          <div className="info-alert">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div>
              <strong>Lote: {inspection.numero_lote}</strong>
              <div>
                {inspection.tipo_muestreo === 'POR_ETAPA' 
                  ? `Configurando ${configurations.length} pallets seleccionados (de ${inspection.cantidad_pallets} totales)`
                  : `Configurando ${configurations.length} pallets`
                }
              </div>
              {inspection.boxes_per_pallet && inspection.boxes_per_pallet.length > 0 && (
                <div style={{ marginTop: '8px', fontSize: '0.9em', color: '#059669' }}>
                  ℹ️ Las cantidades de cajas están pre-cargadas según los valores ingresados en el formulario. 
                  Asegúrese de que coincidan para mantener consistencia con el muestreo.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Botón aplicar a todos */}
        <div className="configuracion-actions-top">
          <button className="btn btn-secondary" onClick={applyToAll}>
            📋 Aplicar Primer Pallet a Todos
          </button>
          <button className="btn btn-secondary" onClick={applyDistribucionToAll}>
            🔄 Aplicar Distribución de Caras a Todos
          </button>
          <div className="total-cajas-display">
            Total cajas: <strong>{getTotalCajas()}</strong>
          </div>
        </div>

        {/* Tabla de configuraciones */}
        <div className="configuracion-content">
          <div className="config-table-container">
            <table className="config-table">
              <thead>
                <tr>
                  <th>Pallet</th>
                  <th>Base (cajas por capa)</th>
                  <th>Cantidad de Cajas</th>
                  <th>Distribución de Caras</th>
                  <th>Capas Calculadas</th>
                </tr>
              </thead>
              <tbody>
                {configurations.map((config, index) => {
                  const base = parseInt(config.base) || 0;
                  const cantidad = parseInt(config.cantidad_cajas) || 0;
                  const capas = base > 0 && cantidad > 0 ? Math.ceil(cantidad / base) : 0;
                  const distribucion = config.distribucion_caras || [];
                  const sumaCaras = distribucion.reduce((sum, cols) => sum + (parseInt(cols) || 0), 0);
                  const distribucionValida = sumaCaras === base && base > 0;
                  
                  return (
                    <tr key={config.numero_pallet}>
                      <td className="pallet-number-cell">
                        <span className="pallet-badge">Pallet {config.numero_pallet}</span>
                      </td>
                      <td>
                        <input
                          type="number"
                          min="1"
                          value={config.base}
                          onChange={(e) => handleConfigChange(index, 'base', e.target.value)}
                          placeholder="Ej: 8"
                          className="config-input"
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          min="1"
                          value={config.cantidad_cajas}
                          onChange={(e) => handleConfigChange(index, 'cantidad_cajas', e.target.value)}
                          placeholder="Ej: 28"
                          className="config-input"
                        />
                      </td>
                      <td>
                        <div className="distribucion-cell">
                          {/* Mostrar template o modo personalizado */}
                          {!config.distribucion_personalizada && base > 0 ? (
                            <div className="distribucion-template">
                              <span className="template-badge">
                                {distribucion.map((cols, idx) => (
                                  <span key={idx}>
                                    Cara {String.fromCharCode(65 + idx)}: {cols}
                                    {idx < distribucion.length - 1 ? ' + ' : ''}
                                  </span>
                                ))}
                              </span>
                              <button
                                type="button"
                                className="btn-icon btn-edit"
                                onClick={() => togglePersonalizado(index)}
                                title="Personalizar distribución"
                              >
                                ✏️
                              </button>
                            </div>
                          ) : base > 0 ? (
                            <div className="distribucion-personalizada">
                              <div className="caras-inputs">
                                {distribucion.map((cols, caraIdx) => (
                                  <div key={caraIdx} className="cara-input-group">
                                    <label className="cara-label">Cara {String.fromCharCode(65 + caraIdx)}</label>
                                    <input
                                      type="number"
                                      min="1"
                                      value={cols}
                                      onChange={(e) => handleDistribucionChange(index, caraIdx, e.target.value)}
                                      className="cara-input"
                                    />
                                    {distribucion.length > 1 && (
                                      <button
                                        type="button"
                                        className="btn-icon btn-remove"
                                        onClick={() => eliminarCara(index, caraIdx)}
                                        title="Eliminar cara"
                                      >
                                        ×
                                      </button>
                                    )}
                                  </div>
                                ))}
                              </div>
                              <div className="distribucion-actions">
                                <button
                                  type="button"
                                  className="btn-icon btn-add"
                                  onClick={() => agregarCara(index)}
                                  title="Agregar cara"
                                >
                                  +
                                </button>
                                <button
                                  type="button"
                                  className="btn-icon btn-reset"
                                  onClick={() => togglePersonalizado(index)}
                                  title="Volver al template"
                                >
                                  ↺
                                </button>
                              </div>
                              {!distribucionValida && (
                                <div className="dist-error">
                                  ⚠️ Suma: {sumaCaras} (debe ser {base})
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="placeholder-text">Ingrese base primero</span>
                          )}
                        </div>
                      </td>
                      <td className="total-cell">
                        <span className={`total-badge ${capas > 0 ? 'has-value' : ''}`}>
                          {capas || '-'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="configuracion-error">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}



        {/* Footer */}
        <div className="configuracion-footer">
          <button className="btn btn-secondary" onClick={handleClose}>
            {inspectionId ? 'Volver' : 'Cancelar'}
          </button>
          <button 
            className="btn btn-success" 
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? (
              <>
                <span className="spinner"></span>
                Guardando...
              </>
            ) : inspectionId ? (
              <>
                ✓ Guardar y Volver
              </>
            ) : (
              <>
                ✓ Guardar y Ver Diagramas
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfiguracionDiagramaView;
