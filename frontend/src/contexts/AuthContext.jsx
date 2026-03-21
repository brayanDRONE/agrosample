/**
 * AuthContext - Maneja la autenticación y el usuario actual
 */

import { createContext, useState, useContext, useEffect } from 'react';
import { apiService } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Cargar usuario al iniciar
  useEffect(() => {
    loadUser();
  }, []);

  // Detectar cambios de sesión (otro usuario inicia sesión en el mismo dispositivo)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'currentUserId') {
        const newUserId = e.newValue;
        const oldUserId = e.oldValue;
        
        // Si el ID de usuario cambió, significa que otro usuario inició sesión en otra pestaña
        if (newUserId && oldUserId && newUserId !== oldUserId) {
          console.warn('Sesión de otro usuario detectada, limpiando autenticación actual');
          setUser(null);
          window.location.href = '/';
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const loadUser = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const hasValidToken = await apiService.ensureValidToken();
      if (!hasValidToken) {
        logout();
        setLoading(false);
        return;
      }

      const userData = await apiService.getCurrentUser();
      setUser(userData);
      // Guardar ID de usuario actual para detectar cambios de sesión
      localStorage.setItem('currentUserId', userData.id);
    } catch (err) {
      console.error('Error al cargar usuario:', err);
      // Si es 401 (token inválido/expirado), limpiar tokens
      if (err.response?.status === 401) {
        console.warn('Token inválido o expirado, limpiando sesión');
        logout();
      } else {
        // Por otros errores, solo hacer logout sin error crítico
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      setError(null);
      const response = await apiService.login(username, password);
      
      // Guardar tokens
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);
      localStorage.setItem('login_at', String(Date.now()));
      
      // Cargar datos completos del usuario
      const userData = await apiService.getCurrentUser();
      setUser(userData);
      
      // Guardar ID de usuario actual para detectar cambios de sesión
      localStorage.setItem('currentUserId', userData.id);
      localStorage.setItem('user', JSON.stringify(userData));
      
      return { success: true, user: userData };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Error al iniciar sesión';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('currentUserId');
    localStorage.removeItem('login_at');
    setUser(null);
  };

  const isSuperAdmin = () => {
    return user?.role === 'SUPERADMIN' || user?.is_superadmin === true;
  };

  const isEstablishmentAdmin = () => {
    return user?.role === 'ESTABLISHMENT_ADMIN' || user?.is_establishment_admin === true;
  };

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    isSuperAdmin,
    isEstablishmentAdmin,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
