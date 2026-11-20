/**
 * useOcrImageUpload
 * Custom hook para procesar imágenes con OCR (Tesseract.js)
 * y extraer números de caja automáticamente.
 */

import { useState, useCallback, useEffect } from 'react';
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

export function findTextRowBounds(rowInkCounts, minInk, maxGap) {
  const rows = [];
  let start = null;
  let end = null;

  for (let y = 0; y < rowInkCounts.length; y++) {
    if (rowInkCounts[y] < minInk) continue;

    if (start === null || y - end > maxGap + 1) {
      if (start !== null) rows.push({ start, end });
      start = y;
    }
    end = y;
  }

  if (start !== null) rows.push({ start, end });
  return rows;
}

export function compareOcrReadings(primary, alternative) {
  const primarySet = new Set(primary);
  const alternativeSet = new Set(alternative);
  return {
    primaryOnly: primary.filter((number) => !alternativeSet.has(number)),
    alternativeOnly: alternative.filter((number) => !primarySet.has(number)),
  };
}

/**
 * Blanquea las líneas oscuras que cruzan casi todo el alto/ancho de la imagen
 * (bordes de tabla). Un dígito nunca ocupa >85% de una fila/columna completa.
 */
function removeTableLines(ctx, x0, y0, w, h, margin) {
  const imgData = ctx.getImageData(x0, y0, w, h);
  const d = imgData.data;
  const isDark = (x, y) => d[(y * w + x) * 4] < 140;

  const lineCols = [];
  for (let x = 0; x < w; x++) {
    let n = 0;
    for (let y = 0; y < h; y++) if (isDark(x, y)) n++;
    if (n / h > 0.85) lineCols.push(x);
  }
  const lineRows = [];
  for (let y = 0; y < h; y++) {
    let n = 0;
    for (let x = 0; x < w; x++) if (isDark(x, y)) n++;
    if (n / w > 0.85) lineRows.push(y);
  }

  const white = (x, y) => {
    const i = (y * w + x) * 4;
    d[i] = d[i + 1] = d[i + 2] = 255;
  };
  for (const c of lineCols) {
    for (let x = Math.max(0, c - margin); x <= Math.min(w - 1, c + margin); x++) {
      for (let y = 0; y < h; y++) white(x, y);
    }
  }
  for (const r of lineRows) {
    for (let y = Math.max(0, r - margin); y <= Math.min(h - 1, r + margin); y++) {
      for (let x = 0; x < w; x++) white(x, y);
    }
  }
  ctx.putImageData(imgData, x0, y0);
}

/**
 * Preprocesa una imagen en un canvas para mejorar la precisión del OCR:
 * - Escala la imagen (Tesseract rinde mejor con imágenes más grandes)
 * - Convierte a escala de grises
 * - Maximiza el contraste (negro/blanco)
 * @param {File} imageFile
 * @returns {Promise<Blob>} Imagen procesada como Blob PNG
 */
export function preprocessImageToCanvas(imageFile, scale = 3) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(imageFile);

    img.onload = () => {
      // Limitar la escala para evitar distorsionar los dígitos y saturar la memoria.
      const SCALE = Math.max(1, Math.min(scale, Math.sqrt(25e6 / (img.width * img.height))));
      const PAD = 80;
      const w = Math.round(img.width * SCALE);
      const h = Math.round(img.height * SCALE);
      const canvas = document.createElement('canvas');
      canvas.width  = w + PAD * 2;
      canvas.height = h + PAD * 2;

      const ctx = canvas.getContext('2d', { willReadFrequently: true });

      // Fondo blanco (también sirve de margen: Tesseract falla con textos pegados al borde)
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Aplicar filtros de forma nativa (grayscale + contraste alto).
      // Esto preserva los bordes suaves de los trazos, evitando
      // que números delgados como "1" desaparezcan con un umbral duro.
      ctx.filter = 'grayscale(1) contrast(2.2) brightness(1.05)';
      ctx.drawImage(img, PAD, PAD, w, h);
      ctx.filter = 'none';

      // Borrar las líneas de borde de tablas/celdas: se fusionan con el primer dígito
      // y hacen que el OCR lo pierda (ej. "62" -> "2", "44" -> "4").
      removeTableLines(ctx, PAD, PAD, w, h, Math.round(SCALE * 2.7));

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

function blobFromCanvas(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error('No se pudo generar la fila preprocesada'));
    }, 'image/png');
  });
}

function splitImageIntoRows(imageBlob, scale) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(imageBlob);

    img.onload = async () => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        ctx.drawImage(img, 0, 0);

        const { data } = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const rowInkCounts = new Array(canvas.height).fill(0);
        for (let y = 0; y < canvas.height; y++) {
          for (let x = 0; x < canvas.width; x++) {
            if (data[(y * canvas.width + x) * 4] < 190) rowInkCounts[y]++;
          }
        }

        const minInk = Math.max(3, Math.floor(canvas.width * 0.001));
        const rowBounds = findTextRowBounds(
          rowInkCounts,
          minInk,
          Math.max(2, Math.round(scale * 2.5))
        );
        const padding = Math.max(8, Math.round(scale * 5));
        const rows = await Promise.all(rowBounds.map(async ({ start, end }) => {
          const top = Math.max(0, start - padding);
          const bottom = Math.min(canvas.height, end + padding + 1);
          const rowCanvas = document.createElement('canvas');
          rowCanvas.width = canvas.width;
          rowCanvas.height = bottom - top;
          rowCanvas.getContext('2d').drawImage(
            canvas,
            0, top, canvas.width, bottom - top,
            0, 0, canvas.width, bottom - top
          );
          return blobFromCanvas(rowCanvas);
        }));

        resolve(rows);
      } catch (error) {
        reject(error);
      } finally {
        URL.revokeObjectURL(url);
      }
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('No se pudo cargar la imagen preprocesada'));
    };

    img.src = url;
  });
}

/**
 * Ejecuta OCR sobre un File/Blob de imagen.
 * @param {File} imageFile
 * @param {(progress: number) => void} onProgress  – Callback 0-100
 * @returns {Promise<string[]>} Textos extraídos en las dos lecturas
 */
export async function runOcr(imageFile, onProgress) {
  const progressState = { scaleIndex: 0, rowIndex: 0, rowCount: 1 };
  const worker = await createWorker('eng', 1, {
    logger: (m) => {
      if (m.status === 'recognizing text' && typeof onProgress === 'function') {
        const scaleProgress = (
          progressState.rowIndex + m.progress
        ) / progressState.rowCount;
        onProgress(Math.round((progressState.scaleIndex + scaleProgress) * 50));
      }
    },
  });

  try {
    await worker.setParameters({
      // PSM 6 preserves the layout when the image has no separate text rows.
      tessedit_pageseg_mode: '6',
    });

    const readings = [];
    for (const [scaleIndex, scale] of [3, 3.5].entries()) {
      progressState.scaleIndex = scaleIndex;
      progressState.rowIndex = 0;
      const imageSource = await preprocessImageToCanvas(imageFile, scale);
      const rowImages = await splitImageIntoRows(imageSource, scale);
      const imagesToRecognize = rowImages.length > 0 ? rowImages : [imageSource];
      progressState.rowCount = imagesToRecognize.length;

      const rowTexts = [];
      for (const rowImage of imagesToRecognize) {
        if (rowImages.length > 0) {
          await worker.setParameters({
            tessedit_pageseg_mode: '7',
            tessedit_char_whitelist: '0123456789',
            preserve_interword_spaces: '1',
          });
        } else {
          await worker.setParameters({
            tessedit_pageseg_mode: '6',
            tessedit_char_whitelist: '',
          });
        }

        const { data: { text } } = await worker.recognize(rowImage);
        rowTexts.push(text);
        progressState.rowIndex++;
      }
      readings.push(rowTexts.join('\n'));
      if (typeof onProgress === 'function') onProgress((scaleIndex + 1) * 50);
    }
    return readings;
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
  const [alternativeNumbers, setAlternativeNumbers] = useState([]);
  const [previewImageUrl, setPreviewImageUrl] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => () => {
    if (previewImageUrl) URL.revokeObjectURL(previewImageUrl);
  }, [previewImageUrl]);

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
    setAlternativeNumbers([]);
    setPreviewImageUrl(null);
    setShowPreview(false);

    try {
      const [primaryText, alternativeText] = await runOcr(file, setOcrProgress);
      const primary = parseOcrNumbers(primaryText);
      const alternative = parseOcrNumbers(alternativeText);
      const numbers = primary.length ? primary : alternative;

      if (numbers.length === 0) {
        setOcrError('No se detectaron números en la imagen. Intenta con una imagen más clara.');
        return;
      }

      setPreviewNumbers(numbers);
      setAlternativeNumbers(primary.length ? alternative : primary);
      setPreviewImageUrl(URL.createObjectURL(file));
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
    setAlternativeNumbers([]);
    setPreviewImageUrl(null);
    setOcrError(null);
  }, []);

  const cancelPreview = useCallback(() => {
    setShowPreview(false);
    setPreviewNumbers([]);
    setAlternativeNumbers([]);
    setPreviewImageUrl(null);
    setOcrError(null);
  }, []);

  const clearError = useCallback(() => setOcrError(null), []);

  return {
    isProcessing,
    ocrProgress,
    ocrError,
    previewNumbers,
    alternativeNumbers,
    previewImageUrl,
    setPreviewNumbers,
    showPreview,
    processImage,
    confirmNumbers,
    cancelPreview,
    clearError,
  };
}
