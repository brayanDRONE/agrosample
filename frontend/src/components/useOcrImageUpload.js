/**
 * useOcrImageUpload
 * Custom hook para procesar imágenes con OCR (Tesseract.js)
 * y extraer números de caja automáticamente.
 */

import { useState, useCallback } from 'react';
import { createWorker } from 'tesseract.js';

// ─── Utilidades ──────────────────────────────────────────────────────────────

/**
 * Extrae únicamente números enteros de un string OCR.
 * Soporta separadores: espacios, saltos de línea, comas, puntos y coma, tabs.
 * Elimina duplicados y valores vacíos.
 * @param {string} rawText - Texto crudo devuelto por OCR
 * @returns {number[]} Array de enteros únicos y válidos
 */
export function parseOcrNumbers(rawText) {
  if (!rawText || typeof rawText !== 'string') return [];

  // Separar por cualquier carácter no-dígito
  const tokens = rawText.split(/[\s,;|\t\r\n]+/);

  const seen = new Set();
  const numbers = [];

  for (const token of tokens) {
    const clean = token.trim();
    if (!clean) continue;

    // Solo aceptar strings que sean íntegramente dígitos
    if (!/^\d+$/.test(clean)) continue;

    const num = parseInt(clean, 10);
    if (isNaN(num) || num <= 0) continue;
    if (seen.has(num)) continue;

    seen.add(num);
    numbers.push(num);
  }

  // Ordenar de menor a mayor
  return numbers.sort((a, b) => a - b);
}

/**
 * Preprocesa una imagen en un canvas para mejorar la precisión del OCR:
 * - Escala al triple (Tesseract rinde mejor con imágenes más grandes)
 * - Convierte a escala de grises
 * - Maximiza el contraste (negro/blanco)
 * @param {File} imageFile
 * @returns {Promise<Blob>} Imagen procesada como Blob PNG
 */
export function preprocessImageToCanvas(imageFile) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(imageFile);

    img.onload = () => {
      const SCALE = 2; // 2x es suficiente y evita presión de memoria
      const canvas = document.createElement('canvas');
      canvas.width  = img.width  * SCALE;
      canvas.height = img.height * SCALE;

      const ctx = canvas.getContext('2d');

      // Fondo blanco
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Aplicar filtros de forma nativa (grayscale + contraste alto).
      // Esto preserva los bordes suaves de los trazos, evitando
      // que números delgados como "1" desaparezcan con un umbral duro.
      ctx.filter = 'grayscale(1) contrast(2.2) brightness(1.05)';
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error('No se pudo generar el blob de imagen preprocesada'));
      }, 'image/png');
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('No se pudo cargar la imagen'));
    };

    img.src = url;
  });
}

/**
 * Ejecuta OCR sobre un File/Blob de imagen.
 * @param {File} imageFile
 * @param {(progress: number) => void} onProgress  – Callback 0-100
 * @returns {Promise<string>} Texto extraído
 */
export async function runOcr(imageFile, onProgress) {
  // Preprocesar la imagen antes de pasarla a Tesseract
  let imageSource;
  try {
    imageSource = await preprocessImageToCanvas(imageFile);
  } catch {
    // Si falla el preprocesamiento, usar la imagen original
    imageSource = imageFile;
  }

  const worker = await createWorker('eng', 1, {
    logger: (m) => {
      if (m.status === 'recognizing text' && typeof onProgress === 'function') {
        onProgress(Math.round(m.progress * 100));
      }
    },
  });

  try {
    await worker.setParameters({
      // PSM 6: bloque uniforme de texto — ideal para tablas en columnas
      tessedit_pageseg_mode: '6',
      // Sin whitelist: dejar que Tesseract lea todo y filtrar números en parseOcrNumbers.
      // El whitelist forzado puede causar que el motor distorsione caracteres.
    });

    const { data: { text } } = await worker.recognize(imageSource);
    return text;
  } finally {
    await worker.terminate();
  }
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useOcrImageUpload() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [ocrProgress, setOcrProgress] = useState(0);
  const [ocrError, setOcrError] = useState(null);
  // Números extraídos pendientes de confirmación
  const [previewNumbers, setPreviewNumbers] = useState([]);
  const [showPreview, setShowPreview] = useState(false);

  /**
   * Procesa una imagen con OCR y carga el resultado en el preview.
   * @param {File} file
   */
  const processImage = useCallback(async (file) => {
    if (!file) return;

    // Validar que sea una imagen
    if (!file.type.startsWith('image/')) {
      setOcrError('El archivo seleccionado no es una imagen válida.');
      return;
    }

    setIsProcessing(true);
    setOcrError(null);
    setOcrProgress(0);
    setPreviewNumbers([]);
    setShowPreview(false);

    try {
      const rawText = await runOcr(file, setOcrProgress);
      const numbers = parseOcrNumbers(rawText);

      if (numbers.length === 0) {
        setOcrError('No se detectaron números en la imagen. Intenta con una imagen más clara.');
        return;
      }

      setPreviewNumbers(numbers);
      setShowPreview(true);
    } catch (err) {
      console.error('OCR error:', err);
      setOcrError('Error al procesar la imagen. Asegúrate de que sea una captura clara.');
    } finally {
      setIsProcessing(false);
      setOcrProgress(0);
    }
  }, []);

  /**
   * Confirma los números del preview y los fusiona con los existentes.
   * @param {number[]} existingNumbers  – números ya presentes en la lista
   * @param {number[]} numbersToAdd     – editados por el usuario en el preview
   * @param {(merged: number[]) => void} onConfirm
   */
  const confirmNumbers = useCallback((existingNumbers, numbersToAdd, onConfirm) => {
    const existingSet = new Set(existingNumbers);
    const merged = [...existingNumbers];

    for (const n of numbersToAdd) {
      if (!existingSet.has(n)) {
        existingSet.add(n);
        merged.push(n);
      }
    }

    // Ordenar de menor a mayor antes de confirmar
    merged.sort((a, b) => a - b);

    onConfirm(merged);
    setShowPreview(false);
    setPreviewNumbers([]);
    setOcrError(null);
  }, []);

  const cancelPreview = useCallback(() => {
    setShowPreview(false);
    setPreviewNumbers([]);
    setOcrError(null);
  }, []);

  const clearError = useCallback(() => setOcrError(null), []);

  return {
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
  };
}
