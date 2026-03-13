/**
 * InspectionForm - Formulario de captura de datos de inspección
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import StageSamplingPanel from './StageSamplingPanel';
import './InspectionForm.css';

function InspectionForm({ onSamplingGenerated, onSubscriptionError }) {
  const { user } = useAuth();
  const [establishments, setEstablishments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] =useState(null);
  
  const [formData, setFormData] = useState({
    exportador: '',
    establecimiento_nombre: '',
    inspector_sag: '',
    contraparte_sag: '',
    especie: '',
    numero_lote: '',
    tamano_lote: '',
    tipo_muestreo: 'NORMAL',
    tipo_despacho: '',
    cantidad_pallets: '',
    boxes_per_pallet: [],
    incremento_intensidad: 0,
  });

  const especies = [
    // Tabla Hipergeométrica (NO permite incremento)
    'Ciruela',
    'Damasco 3%',
    'Damasco 6%',
    'Durazno',
    'Nectarino',
    'Plumcot',
    // Tabla Biométrica (Permite incremento)
    'Clementina',
    'Mandarina', 
    'Tangerina',
    'Manzana',
    'Naranja',
    'Palta',
    'Pera',
    'Pera Asiática',
    'Pomelo',
    // Tabla Porcentual (Permite incremento)
    'Cerezas',
    'Kiwi',
    'Otras',
  ];

  const tiposDespacho = [
    'Inmediato',
    'Pendiente',
    'A Distancia',
  ];

  // Especies por tipo de tabla
  const especiesHipergeometrica = [
    'Ciruela', 'Ciruelas',
    'Damasco', 'Damascos', 'Damasco 3%', 'Damasco 6%',
    'Durazno', 'Duraznos',
    'Nectarino', 'Nectarinos',
    'Plumcot', 'Plumcots'
  ];

  const especiesBiometrica = [
    'Clementina', 'Clementinas',
    'Mandarina', 'Mandarinas',
    'Tangerina', 'Tangerinas',
    'Manzana', 'Manzanas',
    'Naranja', 'Naranjas',
    'Palta', 'Paltas',
    'Pera', 'Peras',
    'Pera Asiática', 'Peras Asiáticas',
    'Pomelo', 'Pomelos',
    'Kiwi', 'Kiwis'
  ];

  /**
   * Determina si una especie permite incremento de intensidad
   */
  const permiteIncrementoIntensidad = (especie) => {
    if (!especie) return false;
    
    const especieNorm = especie.trim().toLowerCase();
    
    // Hipergeométrica NO permite incremento
    const esHipergeometrica = especiesHipergeometrica.some(
      e => e.toLowerCase() === especieNorm
    );
    
    if (esHipergeometrica) return false;
    
    // Biométrica y Porcentual SÍ permiten incremento
    return true;
  };

  useEffect(() => {
    // Ya no cargamos establecimientos del backend ni bloqueamos los campos, 
    // el usuario simplemente escribe el texto.
  }, [user]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Si cambia la especie, verificar si permite incremento
    if (name === 'especie') {
      const permiteIncremento = permiteIncrementoIntensidad(value);
      setFormData(prev => ({
        ...prev,
        [name]: value,
        incremento_intensidad: permiteIncremento ? prev.incremento_intensidad : 0
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
    
    setError(null);
  };

  const handleBoxesPerPalletChange = (boxes) => {
    setFormData(prev => ({
      ...prev,
      boxes_per_pallet: boxes
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validaciones básicas
    if (!formData.establecimiento_nombre) {
      setError('Debe ingresar un establecimiento');
      return;
    }

    if (parseInt(formData.tamano_lote) <= 0) {
      setError('El tamaño del lote debe ser mayor a 0');
      return;
    }

    if (parseInt(formData.cantidad_pallets) <= 0) {
      setError('La cantidad de pallets debe ser mayor a 0');
      return;
    }

    // Validaciones específicas para muestreo por etapa
    if (formData.tipo_muestreo === 'POR_ETAPA') {
      const totalPallets = parseInt(formData.cantidad_pallets);
      const totalBoxesLot = parseInt(formData.tamano_lote);
      
      // Verificar que se hayan ingresado cajas para todos los pallets
      const validBoxes = formData.boxes_per_pallet.filter(b => b > 0);
      if (validBoxes.length !== totalPallets) {
        setError(`Debe ingresar la cantidad de cajas para todos los ${totalPallets} pallets`);
        return;
      }
      
      // Verificar que el total coincida con el tamaño del lote
      const totalEntered = formData.boxes_per_pallet.reduce((sum, val) => sum + val, 0);
      if (totalEntered !== totalBoxesLot) {
        setError(`El total de cajas ingresadas (${totalEntered}) debe ser igual al tamaño del lote (${totalBoxesLot})`);
        return;
      }
      
      // Mínimo 6 pallets
      if (totalPallets < 6) {
        setError('El muestreo por etapa requiere al menos 6 pallets');
        return;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        ...formData,
        tamano_lote: parseInt(formData.tamano_lote),
        cantidad_pallets: parseInt(formData.cantidad_pallets),
        establishment: null, // Ya no enviamos el ID del establecimiento
      };

      // Solo incluir boxes_per_pallet si es muestreo por etapa
      if (formData.tipo_muestreo === 'POR_ETAPA') {
        payload.boxes_per_pallet = formData.boxes_per_pallet;
      } else {
        delete payload.boxes_per_pallet;
      }

      const response = await apiService.generateSampling(payload);

      if (response.success) {
        onSamplingGenerated(response.data);
      } else {
        setError(response.message || 'Error al generar el muestreo');
      }
    } catch (err) {
      console.error('Error:', err);
      
      setError(
        err.response?.data?.message || 
        err.response?.data?.details ||
        'Error al generar el muestreo. Por favor intente nuevamente.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card inspection-form-card">
      <div className="card-header">
        <h2>Nueva Inspección</h2>
        <p>Complete los datos de la inspección para generar el muestreo automático</p>
      </div>

      <form onSubmit={handleSubmit} className="inspection-form">
        {/* Información General */}
        <div className="form-section">
          <h3 className="section-title">Información General</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="exportador">Exportador *</label>
              <input
                type="text"
                id="exportador"
                name="exportador"
                value={formData.exportador}
                onChange={handleChange}
                required
                placeholder="Nombre del exportador"
              />
            </div>

            <div className="form-group">
              <label htmlFor="establecimiento_nombre">Planta/Establecimiento *</label>
              <input
                type="text"
                id="establecimiento_nombre"
                name="establecimiento_nombre"
                value={formData.establecimiento_nombre}
                onChange={handleChange}
                required
                placeholder="Nombre del establecimiento"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="inspector_sag">Inspector SAG *</label>
              <input
                type="text"
                id="inspector_sag"
                name="inspector_sag"
                value={formData.inspector_sag}
                onChange={handleChange}
                required
                placeholder="Nombre del inspector"
              />
            </div>

            <div className="form-group">
              <label htmlFor="contraparte_sag">Contraparte SAG *</label>
              <input
                type="text"
                id="contraparte_sag"
                name="contraparte_sag"
                value={formData.contraparte_sag}
                onChange={handleChange}
                required
                placeholder="Nombre de la contraparte"
              />
            </div>
          </div>
        </div>

        {/* Detalles del Lote */}
        <div className="form-section">
          <h3 className="section-title">Detalles del Lote</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="especie">Especie *</label>
              <select
                id="especie"
                name="especie"
                value={formData.especie}
                onChange={handleChange}
                required
              >
                <option value="">Seleccione...</option>
                {especies.map(esp => (
                  <option key={esp} value={esp}>{esp}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="numero_lote">Número de Lote *</label>
              <input
                type="text"
                id="numero_lote"
                name="numero_lote"
                value={formData.numero_lote}
                onChange={handleChange}
                required
                placeholder="Ej: LOT-2026-001"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="tamano_lote">Tamaño del Lote (cajas) *</label>
              <input
                type="number"
                id="tamano_lote"
                name="tamano_lote"
                value={formData.tamano_lote}
                onChange={handleChange}
                required
                min="1"
                placeholder="Ej: 2332"
              />
            </div>

            <div className="form-group">
              <label htmlFor="cantidad_pallets">Cantidad de Pallets *</label>
              <input
                type="number"
                id="cantidad_pallets"
                name="cantidad_pallets"
                value={formData.cantidad_pallets}
                onChange={handleChange}
                required
                min="1"
                placeholder="Ej: 48"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="tipo_muestreo">Tipo de Muestreo *</label>
              <select
                id="tipo_muestreo"
                name="tipo_muestreo"
                value={formData.tipo_muestreo}
                onChange={handleChange}
                required
              >
                <option value="NORMAL">Normal</option>
                <option value="POR_ETAPA">Por Etapa</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="tipo_despacho">Tipo de Despacho *</label>
              <select
                id="tipo_despacho"
                name="tipo_despacho"
                value={formData.tipo_despacho}
                onChange={handleChange}
                required
              >
                <option value="">Seleccione...</option>
                {tiposDespacho.map(tipo => (
                  <option key={tipo} value={tipo}>{tipo}</option>
                ))}
              </select>
            </div>

            {/* Selector de Incremento de Intensidad */}
            <div className="form-group">
              <label htmlFor="incremento_intensidad">
                Incremento de Intensidad de Muestreo
                {!permiteIncrementoIntensidad(formData.especie) && formData.especie && (
                  <span className="label-info"> (No disponible para esta especie)</span>
                )}
              </label>
              <select
                id="incremento_intensidad"
                name="incremento_intensidad"
                value={formData.incremento_intensidad}
                onChange={handleChange}
                disabled={!permiteIncrementoIntensidad(formData.especie)}
                className={!permiteIncrementoIntensidad(formData.especie) ? 'disabled-select' : ''}
              >
                <option value={0}>Sin incremento</option>
                <option value={20}>+20%</option>
                <option value={40}>+40%</option>
              </select>
              {!permiteIncrementoIntensidad(formData.especie) && formData.especie && (
                <small className="form-help-text warning">
                  ⚠️ Esta especie usa tabla hipergeométrica y no admite incremento de intensidad
                </small>
              )}
              {permiteIncrementoIntensidad(formData.especie) && formData.incremento_intensidad > 0 && (
                <small className="form-help-text info">
                  ℹ️ El tamaño de muestra se incrementará en {formData.incremento_intensidad}%
                </small>
              )}
            </div>
          </div>

          {/* Panel de configuración para muestreo por etapa */}
          {formData.tipo_muestreo === 'POR_ETAPA' && formData.cantidad_pallets && formData.tamano_lote && (
            <StageSamplingPanel
              totalPallets={parseInt(formData.cantidad_pallets) || 0}
              totalBoxesLot={parseInt(formData.tamano_lote) || 0}
              boxesPerPallet={formData.boxes_per_pallet}
              onBoxesPerPalletChange={handleBoxesPerPalletChange}
            />
          )}
        </div>

        {error && (
          <div className="error-message">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}

        <div className="form-actions">
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Generando Muestreo...
              </>
            ) : (
              'Generar Muestreo'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default InspectionForm;
