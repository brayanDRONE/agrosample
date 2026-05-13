/**
 * BatchDescriptionApp - Aplicación para generar planilla de descripción de lote
 */

import { useState } from 'react';
import { ThemeProvider } from '../contexts/ThemeContext';
import Header from './Header';
import BatchDescriptionForm from './BatchDescriptionForm';
import './BatchDescriptionApp.css';

function BatchDescriptionAppContent() {
  const [currentStep, setCurrentStep] = useState('upload'); // upload, type-select, folio-order, data-entry, export
  const [fileData, setFileData] = useState(null);
  const [selectedType, setSelectedType] = useState(null);

  const handleFileLoaded = (data) => {
    setFileData(data);
    setCurrentStep('type-select');
  };

  const handleTypeSelected = (type) => {
    setSelectedType(type);
    // ETAPA requiere el paso de ordenamiento de folios
    if (type === 'ETAPA') {
      setCurrentStep('folio-order');
    } else {
      setCurrentStep('data-entry');
    }
  };

  // Al confirmar el orden de folios para ETAPA, reordenar los pallets en fileData
  const handleFolioOrderConfirmed = (reorderedPallets) => {
    setFileData((prev) => ({ ...prev, pallets: reorderedPallets }));
    setCurrentStep('data-entry');
  };

  const handleGoToTypeSelect = () => {
    setSelectedType(null);
    setCurrentStep('type-select');
  };

  const handleNewBatch = () => {
    setFileData(null);
    setSelectedType(null);
    setCurrentStep('upload');
  };

  return (
    <div className="app">
      <Header />
      
      <main className="main-container">
        <div className="content-wrapper">
          <BatchDescriptionForm
            currentStep={currentStep}
            fileData={fileData}
            selectedType={selectedType}
            onFileLoaded={handleFileLoaded}
            onTypeSelected={handleTypeSelected}
            onFolioOrderConfirmed={handleFolioOrderConfirmed}
            onGoToTypeSelect={handleGoToTypeSelect}
            onNewBatch={handleNewBatch}
          />
        </div>
      </main>
    </div>
  );
}

function BatchDescriptionApp() {
  return (
    <ThemeProvider>
      <BatchDescriptionAppContent />
    </ThemeProvider>
  );
}

export default BatchDescriptionApp;
