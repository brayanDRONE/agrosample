/**
 * batchDescriptionService.js - Servicios API para planilla de descripción
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/batch-description`
  : (import.meta.env.DEV
    ? 'http://localhost:8000/api/batch-description'
    : '/api/batch-description');

const batchDescriptionService = {
  /**
   * Carga y parsea un archivo .INS
   * @param {File} file - Archivo .INS a procesar
   * @returns {Promise} Respuesta de la API con datos parseados
   */
  parseInsFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('access_token');
      const headers = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      // DO NOT set Content-Type for FormData - let axios calculate it with boundary

      const response = await axios.post(
        `${API_BASE_URL}/parse-ins/`,
        formData,
        { headers }
      );
      return response.data;
    } catch (error) {
      console.error('Error parsing INS file:', error);
      throw {
        success: false,
        message: error.response?.data?.message || 'Error al procesar el archivo',
        errors: error.response?.data?.errors || [error.message]
      };
    }
  },

  /**
   * Genera la planilla de descripción de lote
   * @param {Object} data - Datos de la planilla (inspectionType, batchData, certificates)
   * @returns {Promise} Respuesta de la API
   */
  generateBatchDescription: async (data) => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await axios.post(
        `${API_BASE_URL}/generate/`,
        data,
        { headers }
      );
      return response.data;
    } catch (error) {
      console.error('Error generating batch description:', error);
      throw {
        success: false,
        message: error.response?.data?.message || 'Error al generar la planilla',
        errors: error.response?.data?.errors || [error.message]
      };
    }
  },

  /**
   * Exporta la planilla en PDF o Excel
   * @param {Object} data - Datos para exportación (format, batchData, certificates)
   * @returns {Promise} Respuesta con blob del archivo
   */
  exportBatchDescription: async (data) => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await axios.post(
        `${API_BASE_URL}/export/`,
        data,
        {
          headers,
          responseType: 'blob'
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error exporting batch description:', error);
      throw {
        success: false,
        message: error.response?.data?.message || 'Error al exportar la planilla',
        errors: error.response?.data?.errors || [error.message]
      };
    }
  },

  /**
   * Guarda los datos de la planilla y genera un PDF imprimible
   * @param {Object} data - Datos de pallets con certificados
   * @returns {Promise} Respuesta con URL del PDF generado
   */
  saveBatchDescription: async (data) => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await axios.post(
        `${API_BASE_URL}/save-batch/`,
        data,
        { headers }
      );
      return response.data;
    } catch (error) {
      console.error('Error saving batch description:', error);
      throw {
        success: false,
        message: error.response?.data?.message || 'Error al guardar la planilla',
        errors: error.response?.data?.errors || [error.message]
      };
    }
  }
};

export default batchDescriptionService;
