/**
 * OcrImageUpload
 *
 * Botón "📷 Subir Imagen" + modal de preview editable de números extraídos por OCR.
 * Props:
 *   - existingNumbers: number[]           — números ya en la lista principal
 *   - onConfirm: (numbers: number[]) => void — callback con la lista fusionada
 */

import { useRef, useState, useEffect } from 'react';
import { useOcrImageUpload, parseOcrNumbers } from './useOcrImageUpload';

function OcrImageUpload({ existingNumbers = [], onConfirm }) {
  const fileInputRef = useRef(null);

  const {
    isProcessing,
    ocrProgress,
    ocrError,
    previewNumbers,
    setPreviewNumbers,
    showPreview,
    processImage,
    confirmNumbers,
    cancelPreview,
    clearError,
  } = useOcrImageUpload();

  // Texto editable dentro del modal de preview
  const [previewText, setPreviewText] = useState('');

  // Sincronizar previewText con previewNumbers cuando se abre el preview
  useEffect(() => {
    if (showPreview) {
      setPreviewText(previewNumbers.join('\n'));
    }
  }, [showPreview, previewNumbers]);

  // ─── Handlers ──────────────────────────────────────────────────────────────

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      clearError();
      processImage(file);
    }
    // Resetear el input para permitir subir el mismo archivo de nuevo
    e.target.value = '';
  };

  const handleConfirm = () => {
    // Parsear el texto editado como lista de números (uno por línea o separados)
    const editedNumbers = parseOcrNumbers(previewText);

    if (editedNumbers.length === 0) {
      return; // No hacer nada si el usuario borró todo
    }

    confirmNumbers(existingNumbers, editedNumbers, onConfirm);
  };

  // ─── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      {/* Botón disparador + input oculto */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />

      <button
        type="button"
        className="btn btn-upload"
        onClick={() => {
          clearError();
          fileInputRef.current?.click();
        }}
        disabled={isProcessing}
        title="Cargar imagen con números de cajas"
      >
        {isProcessing ? (
          <>
            <span className="ocr-spinner-inline" />
            Leyendo imagen...
          </>
        ) : (
          <>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
            </svg>
            Subir Imagen
          </>
        )}
      </button>

      {/* Barra de progreso durante OCR */}
      {isProcessing && (
        <div className="ocr-progress-bar-container">
          <div
            className="ocr-progress-bar-fill"
            style={{ width: `${ocrProgress}%` }}
          />
          <span className="ocr-progress-label">{ocrProgress}%</span>
        </div>
      )}

      {/* Error inline (fuera del modal) */}
      {ocrError && !showPreview && (
        <div className="ocr-error-inline" role="alert">
          <span>⚠️ {ocrError}</span>
          <button
            type="button"
            className="ocr-error-close"
            onClick={clearError}
            aria-label="Cerrar error"
          >
            ✕
          </button>
        </div>
      )}

      {/* Modal de preview */}
      {showPreview && (
        <div className="ocr-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="ocr-modal-title">
          <div className="ocr-modal">
            <div className="ocr-modal-header">
              <h3 id="ocr-modal-title">
                📋 Números detectados por OCR
              </h3>
              <p className="ocr-modal-subtitle">
                Revisa y edita los números antes de confirmar. Uno por línea.
              </p>
            </div>

            <div className="ocr-modal-body">
              <div className="ocr-preview-stats">
                <span className="ocr-stat-badge">
                  {parseOcrNumbers(previewText).length} número(s) detectado(s)
                </span>
                {existingNumbers.length > 0 && (
                  <span className="ocr-stat-badge ocr-stat-existing">
                    {existingNumbers.length} ya en lista
                  </span>
                )}
              </div>

              <textarea
                className="ocr-preview-textarea"
                value={previewText}
                onChange={(e) => setPreviewText(e.target.value)}
                rows={Math.min(Math.max(previewNumbers.length + 2, 6), 16)}
                spellCheck={false}
                aria-label="Números extraídos de la imagen"
              />

              <p className="ocr-modal-hint">
                💡 Separa números por líneas, espacios o comas. Se eliminarán duplicados automáticamente.
              </p>
            </div>

            <div className="ocr-modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={cancelPreview}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="btn btn-success"
                onClick={handleConfirm}
                disabled={parseOcrNumbers(previewText).length === 0}
              >
                ✓ Confirmar ({parseOcrNumbers(previewText).length})
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default OcrImageUpload;
