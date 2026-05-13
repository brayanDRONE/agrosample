/**
 * FolioOrderPanel - Ordenamiento manual de folios para muestreo Por Etapa
 *
 * Interacción:
 *  - Click izquierdo en folio disponible → agrega al orden (al final)
 *  - Click derecho en folio ordenado → devuelve a disponibles
 *  - Drag & drop dentro de la lista ordenada → cambia posición
 */

import { useState, useRef } from 'react';
import './FolioOrderPanel.css';

function FolioOrderPanel({ pallets = [], onConfirm, onBack }) {
  // Todos los folios (en el orden original del archivo)
  const allFolios = pallets.map((p) => p.folio_pallet);

  // Estado: folios en cola de orden definido por el usuario
  const [orderedFolios, setOrderedFolios] = useState([]);

  // Folios que aún no han sido ordenados
  const availableFolios = allFolios.filter((f) => !orderedFolios.includes(f));

  // ─── Drag & drop dentro de la lista ordenada ──────────────────────────────
  const dragIndex = useRef(null);
  const dragOverIndex = useRef(null);

  const handleDragStart = (e, index) => {
    dragIndex.current = index;
    e.dataTransfer.effectAllowed = 'move';
    // Pequeño timeout para que el "ghost" aparezca antes de aplicar la clase
    setTimeout(() => {
      e.target.classList.add('dragging');
    }, 0);
  };

  const handleDragEnd = (e) => {
    e.target.classList.remove('dragging');
    dragIndex.current = null;
    dragOverIndex.current = null;
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    dragOverIndex.current = index;
  };

  const handleDrop = (e, index) => {
    e.preventDefault();
    if (dragIndex.current === null || dragIndex.current === index) return;

    const newOrder = [...orderedFolios];
    const [moved] = newOrder.splice(dragIndex.current, 1);
    newOrder.splice(index, 0, moved);
    setOrderedFolios(newOrder);
  };

  // ─── Agregar folio al orden (click izquierdo en disponible) ───────────────
  const handleAddFolio = (folio) => {
    setOrderedFolios((prev) => [...prev, folio]);
  };

  // ─── Quitar folio del orden (click derecho en ordenado) ───────────────────
  const handleRemoveFolio = (e, folio) => {
    e.preventDefault(); // evitar menú contextual del navegador
    setOrderedFolios((prev) => prev.filter((f) => f !== folio));
  };

  // ─── Agregar todos de una vez ─────────────────────────────────────────────
  const handleAddAll = () => {
    setOrderedFolios(allFolios);
  };

  // ─── Limpiar todo ─────────────────────────────────────────────────────────
  const handleClearAll = () => {
    setOrderedFolios([]);
  };

  // ─── Confirmar orden ─────────────────────────────────────────────────────
  const handleConfirm = () => {
    if (orderedFolios.length !== allFolios.length) return;
    // Reordenar el array de pallets según el orden definido
    const reordered = orderedFolios.map((folio) =>
      pallets.find((p) => p.folio_pallet === folio)
    );
    onConfirm(reordered);
  };

  const isComplete = orderedFolios.length === allFolios.length;
  const progress = allFolios.length > 0 ? (orderedFolios.length / allFolios.length) * 100 : 0;

  return (
    <div className="folio-order-panel">
      {/* ── Encabezado ── */}
      <div className="fop-header">
        <div className="fop-header-icon">🧊</div>
        <div>
          <h2>Ordenar Folios — Posición en Cámara de Frío</h2>
          <p className="fop-subtitle">
            Defina el orden exacto en que los pallets están ubicados físicamente
            en la cámara. Este orden se reflejará en la planilla generada.
          </p>
        </div>
      </div>

      {/* ── Instrucciones ── */}
      <div className="fop-instructions">
        <div className="fop-hint">
          <span className="fop-hint-key left-click">Click izquierdo</span>
          sobre un folio disponible para añadirlo al orden
        </div>
        <div className="fop-hint">
          <span className="fop-hint-key right-click">Click derecho</span>
          sobre un folio ordenado para devolverlo
        </div>
        <div className="fop-hint">
          <span className="fop-hint-key drag">⠿ Arrastrar</span>
          dentro de la lista para cambiar posición
        </div>
      </div>

      {/* ── Barra de progreso ── */}
      <div className="fop-progress-wrap">
        <div className="fop-progress-bar">
          <div
            className={`fop-progress-fill ${isComplete ? 'complete' : ''}`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="fop-progress-label">
          {orderedFolios.length} / {allFolios.length} folios ordenados
        </span>
      </div>

      {/* ── Cuerpo dividido en dos paneles ── */}
      <div className="fop-body">

        {/* ── Panel izquierdo: Disponibles ── */}
        <div className="fop-section available-section">
          <div className="fop-section-header">
            <h3>
              <span className="fop-section-dot available-dot" />
              Disponibles
              <span className="fop-count-badge">{availableFolios.length}</span>
            </h3>
            <button
              className="fop-action-btn"
              onClick={handleAddAll}
              disabled={availableFolios.length === 0}
              title="Agregar todos al orden"
            >
              Agregar todos ↓
            </button>
          </div>

          <div className="fop-chips-grid">
            {availableFolios.length === 0 ? (
              <div className="fop-empty-state">
                <span>✓ Todos los folios han sido ordenados</span>
              </div>
            ) : (
              availableFolios.map((folio) => (
                <button
                  key={folio}
                  className="fop-chip available-chip"
                  onClick={() => handleAddFolio(folio)}
                  title="Click para agregar al orden"
                >
                  <span className="fop-chip-icon">📦</span>
                  <span className="fop-chip-folio">{folio}</span>
                  <span className="fop-chip-arrow">→</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* ── Separador central ── */}
        <div className="fop-divider">
          <div className="fop-divider-line" />
          <div className="fop-divider-icon">⇄</div>
          <div className="fop-divider-line" />
        </div>

        {/* ── Panel derecho: Orden definido ── */}
        <div className="fop-section ordered-section">
          <div className="fop-section-header">
            <h3>
              <span className="fop-section-dot ordered-dot" />
              Orden en Cámara
              <span className="fop-count-badge ordered">{orderedFolios.length}</span>
            </h3>
            <button
              className="fop-action-btn danger"
              onClick={handleClearAll}
              disabled={orderedFolios.length === 0}
              title="Limpiar todo el orden"
            >
              Limpiar todo ✕
            </button>
          </div>

          <div className="fop-ordered-list">
            {orderedFolios.length === 0 ? (
              <div className="fop-empty-state">
                <span>Haga click en los folios de la izquierda para ordenarlos</span>
              </div>
            ) : (
              orderedFolios.map((folio, index) => (
                <div
                  key={folio}
                  className="fop-ordered-item"
                  draggable
                  onDragStart={(e) => handleDragStart(e, index)}
                  onDragEnd={handleDragEnd}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDrop={(e) => handleDrop(e, index)}
                  onContextMenu={(e) => handleRemoveFolio(e, folio)}
                  title="Arrastre para reordenar · Click derecho para devolver"
                >
                  <span className="fop-position-badge">{index + 1}</span>
                  <span className="fop-drag-handle">⠿</span>
                  <span className="fop-chip-icon">📦</span>
                  <span className="fop-ordered-folio">{folio}</span>
                  <button
                    className="fop-remove-btn"
                    onClick={(e) => handleRemoveFolio(e, folio)}
                    title="Quitar del orden"
                  >
                    ✕
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* ── Validación y acciones ── */}
      {!isComplete && orderedFolios.length > 0 && (
        <div className="fop-warning">
          ⚠️ Faltan <strong>{availableFolios.length}</strong> folio(s) por ordenar
          antes de continuar.
        </div>
      )}

      {isComplete && (
        <div className="fop-success">
          ✓ Todos los folios están ordenados. Puede continuar al ingreso de certificados.
        </div>
      )}

      <div className="fop-actions">
        <button className="fop-btn-back" onClick={onBack}>
          ← Cambiar tipo de muestreo
        </button>
        <button
          className={`fop-btn-confirm ${isComplete ? 'enabled' : 'disabled'}`}
          onClick={handleConfirm}
          disabled={!isComplete}
        >
          Confirmar orden y continuar →
        </button>
      </div>
    </div>
  );
}

export default FolioOrderPanel;
