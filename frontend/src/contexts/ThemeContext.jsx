/**
 * ThemeContext - Gestión de temas dinámicos por establecimiento
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import apiService from '../services/api';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export function ThemeProvider({ children }) {
  const { user } = useAuth();
  const [theme, setTheme] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTheme();
  }, [user]);

  const loadTheme = async () => {
    // Tema por defecto adaptado a los colores de la página de inicio (Landing)
    const defaultTheme = {
      primary_color: '#008a45',
      secondary_color: '#003d2b',
      accent_color: '#83e635',
      company_name: user?.establishment?.nombre || 'agrosample',
      welcome_message: 'Automatización de etiquetas y diagramas adaptables',
      show_logo: true,
      dark_mode: false
    };

    if (!user || !user.establishment) {
      setTheme(defaultTheme);
      applyTheme(defaultTheme);
      setLoading(false);
      return;
    }

    try {
      // Usar endpoint público para obtener el tema del establecimiento
      const themeData = await apiService.getMyTheme();
      setTheme(themeData);
      applyTheme(themeData);
    } catch (err) {
      console.error('Error loading theme:', err);
      // Si falla, usa tema por defecto
      setTheme(defaultTheme);
      applyTheme(defaultTheme);
    } finally {
      setLoading(false);
    }
  };

  const applyTheme = (themeData) => {
    if (!themeData) return;

    const root = document.documentElement;
    
    // Aplicar colores como variables CSS
    root.style.setProperty('--theme-primary', themeData.primary_color || '#008a45');
    root.style.setProperty('--theme-secondary', themeData.secondary_color || '#003d2b');
    root.style.setProperty('--theme-accent', themeData.accent_color || '#83e635');
    
    // Crear versiones con transparencia
    const primary = themeData.primary_color || '#008a45';
    const secondary = themeData.secondary_color || '#003d2b';
    const accent = themeData.accent_color || '#83e635';
    
    root.style.setProperty('--theme-primary-rgb', hexToRgb(primary));
    root.style.setProperty('--theme-secondary-rgb', hexToRgb(secondary));
    root.style.setProperty('--theme-accent-rgb', hexToRgb(accent));
    
    // Aplicar gradiente principal
    root.style.setProperty(
      '--theme-gradient',
      `linear-gradient(135deg, ${primary} 0%, ${secondary} 100%)`
    );
    
    // Aplicar modo oscuro si está habilitado
    if (themeData.dark_mode) {
      root.classList.add('dark-mode');
    } else {
      root.classList.remove('dark-mode');
    }
  };

  const hexToRgb = (hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
      : '0, 138, 69'; // default primary color RGB
  };

  const refreshTheme = async () => {
    await loadTheme();
  };

  const value = {
    theme,
    loading,
    refreshTheme,
    applyTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}
