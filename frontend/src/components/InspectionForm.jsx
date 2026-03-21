/**
 * InspectionForm - Formulario simplificado para registrar lote
 */

import { useState } from 'react';
import { apiService } from '../services/api';
import './InspectionForm.css';

function InspectionForm({ onSamplingGenerated, onSubscriptionError }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    numero_lote: '',
    cantidad_pallets: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.numero_lote.trim()) {
      setError('Debe ingresar el número de lote');
      return;
    }

    if (parseInt(formData.cantidad_pallets) <= 0) {
      setError('La cantidad de pallets debe ser mayor a 0');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        numero_lote: formData.numero_lote.trim(),
        cantidad_pallets: parseInt(formData.cantidad_pallets),
        tamano_lote: parseInt(formData.cantidad_pallets),
        tipo_muestreo: 'NORMAL',
        exportador: 'N/A',
        establecimiento_nombre: 'N/A',
        inspector_sag: 'N/A',
        contraparte_sag: 'N/A',
        especie: 'N/A',
        tipo_despacho: 'N/A',
      };

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
        <h2>Registro de Lote</h2>
        <p>Ingrese número de lote y cantidad de pallets para continuar al panel de configuración</p>
      </div>

      <form onSubmit={handleSubmit} className="inspection-form">
        <div className="form-section">
          <h3 className="section-title">Datos Iniciales</h3>
          
          <div className="form-row">
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
                Registrando Lote...
              </>
            ) : (
              'Continuar muestreo'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default InspectionForm;
