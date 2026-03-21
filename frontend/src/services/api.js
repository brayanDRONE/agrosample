/**
 * API Service - Maneja todas las llamadas al backend Django
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL
  || (import.meta.env.DEV
    ? 'http://localhost:8000/api'
    : '/api');

const MAX_SESSION_DURATION_MS = 8 * 60 * 60 * 1000;

const clearAuthStorage = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  localStorage.removeItem('currentUserId');
  localStorage.removeItem('login_at');
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const isTokenExpired = (token) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const now = Date.now();
    const expMs = (payload.exp || 0) * 1000;
    // Considerar expirado si faltan <= 5 segundos para vencer
    return expMs <= now + 5000;
  } catch {
    return true;
  }
};

const parseTokenPayload = (token) => {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
};

const hasExceededSessionDuration = () => {
  const loginAtRaw = localStorage.getItem('login_at');
  let loginAt = Number(loginAtRaw);

  if (!Number.isFinite(loginAt) || loginAt <= 0) {
    const token = localStorage.getItem('access_token');
    const payload = token ? parseTokenPayload(token) : null;
    loginAt = payload?.iat ? payload.iat * 1000 : Date.now();
    localStorage.setItem('login_at', String(loginAt));
  }

  return Date.now() - loginAt >= MAX_SESSION_DURATION_MS;
};

const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) return null;

  const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
    refresh: refreshToken
  });

  const { access } = response.data;
  localStorage.setItem('access_token', access);
  return access;
};

// Interceptor para agregar token JWT a las peticiones
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si el error es 401 y no hemos intentado renovar el token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (hasExceededSessionDuration()) {
        clearAuthStorage();
        window.location.href = '/';
        return Promise.reject(error);
      }

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          // Reintentar la petición original
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Si falla el refresh, limpiar tokens y redirigir al login
        clearAuthStorage();
        window.location.href = '/';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Servicios de API
export const apiService = {
  async ensureValidToken() {
    const token = localStorage.getItem('access_token');
    if (!token) return false;

    if (hasExceededSessionDuration()) {
      clearAuthStorage();
      return false;
    }

    if (!isTokenExpired(token)) {
      return true;
    }

    try {
      const newAccess = await refreshAccessToken();
      return !!newAccess;
    } catch {
      clearAuthStorage();
      return false;
    }
  },

  // ========== Autenticación ==========
  async login(username, password) {
    const response = await api.post('/auth/login/', { username, password });
    return response.data;
  },

  async getCurrentUser() {
    const response = await api.get('/users/current/me/');
    return response.data;
  },

  // ========== Establecimientos (Público) ==========
  async getEstablishments() {
    const response = await api.get('/establishments/');
    return response.data;
  },

  // ========== Muestreo ==========
  async generateSampling(data) {
    const response = await api.post('/muestreo/generar/', data);
    return response.data;
  },

  // ========== Inspecciones ==========
  async getInspections() {
    const response = await api.get('/inspections/');
    return response.data;
  },

  async getSamplingResult(id) {
    const response = await api.get(`/sampling-results/${id}/`);
    return response.data;
  },

  // ========== ADMIN: Dashboard ==========
  async getAdminStats() {
    const response = await api.get('/admin/dashboard/stats/');
    return response.data;
  },

  async getRecentActivity() {
    const response = await api.get('/admin/dashboard/recent_activity/');
    return response.data;
  },

  // ========== ADMIN: Establecimientos ==========
  async getAllEstablishments() {
    const response = await api.get('/admin/establishments/');
    return response.data;
  },

  async getEstablishmentById(id) {
    const response = await api.get(`/admin/establishments/${id}/`);
    return response.data;
  },

  async getEstablishmentsByFilter(filter) {
    const filterMap = {
      'active': '/admin/establishments/active/',
      'expiring_soon': '/admin/establishments/expiring_soon/',
      'expired': '/admin/establishments/expired/'
    };
    const endpoint = filterMap[filter] || '/admin/establishments/';
    const response = await api.get(endpoint);
    return response.data;
  },

  async getActiveEstablishments() {
    const response = await api.get('/admin/establishments/active/');
    return response.data;
  },

  async getExpiringSoonEstablishments() {
    const response = await api.get('/admin/establishments/expiring_soon/');
    return response.data;
  },

  async getExpiredEstablishments() {
    const response = await api.get('/admin/establishments/expired/');
    return response.data;
  },

  async createEstablishment(data) {
    const response = await api.post('/admin/establishments/', data);
    return response.data;
  },

  async updateEstablishment(id, data) {
    const response = await api.patch(`/admin/establishments/${id}/`, data);
    return response.data;
  },

  async deleteEstablishment(id) {
    const response = await api.delete(`/admin/establishments/${id}/`);
    return response.data;
  },

  async renewSubscription(id, days = 30) {
    const response = await api.post(`/admin/establishments/${id}/renew_subscription/`, { days });
    return response.data;
  },

  async suspendEstablishment(id) {
    const response = await api.post(`/admin/establishments/${id}/suspend/`);
    return response.data;
  },

  async activateEstablishment(id) {
    const response = await api.post(`/admin/establishments/${id}/activate/`);
    return response.data;
  },

  // ========== ADMIN: Temas ==========
  async getTheme(establishmentId) {
    const response = await api.get(`/admin/themes/by_establishment/?establishment_id=${establishmentId}`);
    return response.data;
  },

  async getMyTheme() {
    const response = await api.get('/themes/my-theme/');
    return response.data;
  },

  async updateTheme(id, data) {
    const response = await api.patch(`/admin/themes/${id}/`, data);
    return response.data;
  },
};

export default apiService;
