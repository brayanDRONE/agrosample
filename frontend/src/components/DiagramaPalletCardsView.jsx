/**
 * DiagramaPalletCardsView - Vista de pallets en formato tarjetas estilo INACAP
 * 
 * Muestra todos los pallets como tarjetas en un grid responsivo
 * similar a la interfaz de INACAP.
 */

import { useState, useEffect, useCallback } from 'react';
import DiagramaPalletCard from './DiagramaPalletCard';
import DiagramaPallet from './DiagramaPallet';
import ConfiguracionDiagramaView from './ConfiguracionDiagramaView';
import './DiagramaPalletCardsView.css';

function DiagramaPalletCardsView({ inspection, onClose }) {
  const [pallets, setPallets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPallet, setSelectedPallet] = useState(null);
  const [inspectionData, setInspectionData] = useState(null);
  const [viewMode, setViewMode] = useState('cards'); // 'cards' o 'detail'
  const [requiresConfiguration, setRequiresConfiguration] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [deleting, setDeleting] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    if (inspection && inspection.id) {
      loadPallets();
    }
  }, [inspection?.id]);

  const loadPallets = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(
        `${API_URL}/muestreo/diagrama-pallets/${inspection.id}/`,
        { headers }
      );

      const data = await response.json();

      // Verificar si requiere configuración (antes de verificar response.ok)
      if (data.requires_configuration) {
        console.info('ℹ️ Configuración de pallets requerida - Mostrando modal de configuración');
        setRequiresConfiguration(true);
        setLoading(false);
        return;
      }

      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Error al obtener datos de diagrama');
      }

      const palletsLoaded = data.data.pallets || [];
      console.log('✅ Pallets cargados:', palletsLoaded);
      
      setPallets(palletsLoaded);
      setInspectionData(data.data.inspection || null);
      setRequiresConfiguration(false);
      
      if (palletsLoaded.length === 0) {
        console.warn('⚠️ No hay pallets en la respuesta del servidor');
      }
    } catch (err) {
      console.error('Error loading pallets:', err);
      setError('No se pudieron cargar los pallets. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleExpandPallet = (pallet) => {
    setSelectedPallet(pallet);
    setViewMode('detail');
  };

  const handleBack = () => {
    setViewMode('cards');
    setSelectedPallet(null);
  };

  const handleDeletePallet = (pallet) => {
    if (confirm(`¿Estás seguro de que deseas eliminar el Pallet ${pallet.numero_pallet}?`)) {
      console.log('Eliminar pallet:', pallet.numero_pallet);
    }
  };

  const handleEditPallet = (pallet) => {
    console.log('Editar pallet:', pallet.numero_pallet);
  };

  const handleConfigurationCompleted = () => {
    // Después de configurar, volver a cargar los datos del diagrama
    console.log('✅ handleConfigurationCompleted ejecutado');
    setRequiresConfiguration(false);
    setLoading(true); // Asegurar que loading esté true cuando recargamos
    loadPallets();
  };

  if (loading) {
    return (
      <div className="pallets-view-container modal-overlay">
        <div className="modal-content">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Cargando pallets...</p>
          </div>
        </div>
      </div>
    );
  }

  if (requiresConfiguration) {
    return (
      <ConfiguracionDiagramaView
        inspection={inspection}
        onClose={onClose}
        onConfigured={handleConfigurationCompleted}
      />
    );
  }

  if (error) {
    return (
      <div className="pallets-view-container modal-overlay">
        <div className="modal-content">
          <button onClick={onClose} className="modal-close">×</button>
          <div className="error-message">
            <p>{error}</p>
            <button onClick={loadPallets} className="retry-button">
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (viewMode === 'detail' && selectedPallet) {
    return (
      <div className="pallets-view-container modal-overlay">
        <div className="modal-content modal-large">
          <button onClick={handleBack} className="modal-close">×</button>
          <button onClick={handleBack} className="back-button">
            ← Volver a tarjetas
          </button>
          <div style={{ padding: '20px' }}>
            <DiagramaPallet
              palletData={selectedPallet}
              basePallet={selectedPallet.base}
              alturaPallet={selectedPallet.altura}
              distribucionCaras={selectedPallet.distribucion_caras || []}
              inspectionNumber={inspectionData?.numero_lote}
            />
          </div>
        </div>
      </div>
    );
  }

  if (pallets.length === 0) {
    return (
      <div className="pallets-view-container modal-overlay">
        <div className="modal-content">
          <button onClick={onClose} className="modal-close">×</button>
          <div className="empty-state">
            <p>No hay pallets disponibles</p>
            <button onClick={onClose} className="retry-button">Cerrar</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pallets-view-container modal-overlay">
      <div className="modal-content">
        <button onClick={onClose} className="modal-close">×</button>
        
        <div className="cards-header">
          <h2>Pallets Disponibles</h2>
          <p className="cards-subtitle">{pallets.length} pallet{pallets.length !== 1 ? 's' : ''} registrado{pallets.length !== 1 ? 's' : ''}</p>
        </div>

        <div className="pallet-cards-grid">
          {pallets.map((pallet, idx) => (
            <DiagramaPalletCard
              key={pallet.id || `pallet-${idx}`}
              palletData={pallet}
              onExpand={handleExpandPallet}
              onDelete={handleDeletePallet}
              onEdit={handleEditPallet}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default DiagramaPalletCardsView;
