/**
 * ThemeEditor - Editor de personalización de temas para establecimientos
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/api';
import './ThemeEditor.css';

function ThemeEditor() {
  const { establishmentId } = useParams();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [establishment, setEstablishment] = useState(null);
  const [theme, setTheme] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [previewMode, setPreviewMode] = useState(false);
  
  const [formData, setFormData] = useState({
    primary_color: '#667eea',
    secondary_color: '#764ba2',
    accent_color: '#f56565',
    company_name: '',
    welcome_message: '',
    footer_text: '',
    show_logo: true,
    dark_mode: false
  });

  useEffect(() => {
    loadThemeData();
  }, [establishmentId]);

  const loadThemeData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [estData, themeData] = await Promise.all([
        apiService.getEstablishmentById(establishmentId),
        apiService.getTheme(establishmentId)
      ]);

      setEstablishment(estData);
      setTheme(themeData);
      
      if (themeData) {
        setFormData({
          primary_color: themeData.primary_color || '#667eea',
          secondary_color: themeData.secondary_color || '#764ba2',
          accent_color: themeData.accent_color || '#f56565',
          company_name: themeData.company_name || '',
          welcome_message: themeData.welcome_message || '',
          footer_text: themeData.footer_text || '',
          show_logo: themeData.show_logo ?? true,
          dark_mode: themeData.dark_mode ?? false
        });
      }
    } catch (err) {
      console.error('Error loading theme data:', err);
      setError('Error al cargar los datos del tema');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      await apiService.updateTheme(theme.id, formData);
      alert('Tema actualizado exitosamente');
      navigate('/admin/establishments');
    } catch (err) {
      console.error('Error saving theme:', err);
      alert('Error al guardar el tema');
    } finally {
      setSaving(false);
    }
  };

  const handleColorChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const applyPreviewStyles = () => {
    if (!previewMode) return {};
    
    return {
      '--primary-color': formData.primary_color,
      '--secondary-color': formData.secondary_color,
      '--accent-color': formData.accent_color
    };
  };

  if (loading) {
    return (
      <div className="theme-editor-loading">
        <div className="spinner-large"></div>
        <p>Cargando editor de temas...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="theme-editor-error">
        <p>{error}</p>
        <button onClick={loadThemeData} className="btn btn-primary">
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="theme-editor" style={applyPreviewStyles()}>
      {/* Header */}
      <header className="theme-editor-header">
        <div className="header-content">
          <div className="header-left">
            <button onClick={() => navigate('/admin/establishments')} className="btn-back">
              ← Volver a Establecimientos
            </button>
            <div>
              <h1>Editor de Tema</h1>
              <p>{establishment?.nombre}</p>
            </div>
          </div>
          <div className="header-right">
            <button 
              onClick={() => setPreviewMode(!previewMode)}
              className={`btn ${previewMode ? 'btn-primary' : 'btn-secondary'}`}
            >
              {previewMode ? '✓ Vista Previa' : 'Ver Previa'}
            </button>
            <button onClick={() => { logout(); navigate('/'); }} className="btn btn-secondary">
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="theme-editor-main">
        <div className="editor-container">
          <div className="editor-grid">
            {/* Form Column */}
            <div className="editor-form-column">
              <form onSubmit={handleSubmit}>
                {/* Colors Section */}
                <div className="form-section">
                  <h2 className="section-title">Colores</h2>
                  <div className="color-inputs">
                    <div className="color-input-group">
                      <label>Color Primario</label>
                      <div className="color-input-wrapper">
                        <input
                          type="color"
                          value={formData.primary_color}
                          onChange={(e) => handleColorChange('primary_color', e.target.value)}
                          className="color-picker"
                        />
                        <input
                          type="text"
                          value={formData.primary_color}
                          onChange={(e) => handleColorChange('primary_color', e.target.value)}
                          className="color-text"
                          pattern="^#[0-9A-Fa-f]{6}$"
                        />
                      </div>
                    </div>

                    <div className="color-input-group">
                      <label>Color Secundario</label>
                      <div className="color-input-wrapper">
                        <input
                          type="color"
                          value={formData.secondary_color}
                          onChange={(e) => handleColorChange('secondary_color', e.target.value)}
                          className="color-picker"
                        />
                        <input
                          type="text"
                          value={formData.secondary_color}
                          onChange={(e) => handleColorChange('secondary_color', e.target.value)}
                          className="color-text"
                          pattern="^#[0-9A-Fa-f]{6}$"
                        />
                      </div>
                    </div>

                    <div className="color-input-group">
                      <label>Color de Acento</label>
                      <div className="color-input-wrapper">
                        <input
                          type="color"
                          value={formData.accent_color}
                          onChange={(e) => handleColorChange('accent_color', e.target.value)}
                          className="color-picker"
                        />
                        <input
                          type="text"
                          value={formData.accent_color}
                          onChange={(e) => handleColorChange('accent_color', e.target.value)}
                          className="color-text"
                          pattern="^#[0-9A-Fa-f]{6}$"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Branding Section */}
                <div className="form-section">
                  <h2 className="section-title">Marca</h2>
                  <div className="form-group">
                    <label>Nombre de la Compañía</label>
                    <input
                      type="text"
                      value={formData.company_name}
                      onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                      placeholder={establishment?.nombre}
                    />
                  </div>
                  <div className="form-group">
                    <label>Mensaje de Bienvenida</label>
                    <textarea
                      value={formData.welcome_message}
                      onChange={(e) => setFormData({ ...formData, welcome_message: e.target.value })}
                      placeholder="Bienvenido a nuestro sistema"
                      rows={3}
                    />
                  </div>
                  <div className="form-group">
                    <label>Texto del Footer</label>
                    <input
                      type="text"
                      value={formData.footer_text}
                      onChange={(e) => setFormData({ ...formData, footer_text: e.target.value })}
                      placeholder="© 2024 - Todos los derechos reservados"
                    />
                  </div>
                </div>

                {/* Display Options */}
                <div className="form-section">
                  <h2 className="section-title">Opciones de Visualización</h2>
                  <div className="checkbox-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.show_logo}
                        onChange={(e) => setFormData({ ...formData, show_logo: e.target.checked })}
                      />
                      <span>Mostrar logo</span>
                    </label>
                  </div>
                  <div className="checkbox-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.dark_mode}
                        onChange={(e) => setFormData({ ...formData, dark_mode: e.target.checked })}
                      />
                      <span>Modo oscuro (experimental)</span>
                    </label>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="form-actions">
                  <button
                    type="button"
                    onClick={() => navigate('/admin/establishments')}
                    className="btn btn-secondary"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={saving}
                  >
                    {saving ? (
                      <>
                        <span className="spinner-sm"></span>
                        Guardando...
                      </>
                    ) : (
                      'Guardar Cambios'
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Preview Column */}
            <div className="editor-preview-column">
              <div className="preview-container">
                <h3 className="preview-title">Vista Previa</h3>
                
                {previewMode ? (
                  <div className="preview-content" style={applyPreviewStyles()}>
                    {/* Header Preview */}
                    <div 
                      className="preview-header"
                      style={{ 
                        background: `linear-gradient(135deg, ${formData.primary_color} 0%, ${formData.secondary_color} 100%)`
                      }}
                    >
                      <div className="preview-header-content">
                        {formData.show_logo && (
                          <div className="preview-logo">LOGO</div>
                        )}
                        <h2>{formData.company_name || establishment?.nombre}</h2>
                      </div>
                    </div>

                    {/* Welcome Message */}
                    {formData.welcome_message && (
                      <div className="preview-welcome">
                        <p>{formData.welcome_message}</p>
                      </div>
                    )}

                    {/* Sample Content */}
                    <div className="preview-sample-content">
                      <div className="preview-card">
                        <h3>Tarjeta de Ejemplo</h3>
                        <p>Este es un ejemplo de cómo se verán las tarjetas con los colores seleccionados.</p>
                        <button 
                          className="preview-button"
                          style={{ 
                            background: `linear-gradient(135deg, ${formData.primary_color} 0%, ${formData.secondary_color} 100%)` 
                          }}
                        >
                          Botón de Acción
                        </button>
                      </div>

                      <div className="preview-badges">
                        <span 
                          className="preview-badge"
                          style={{ backgroundColor: formData.primary_color + '20', color: formData.primary_color }}
                        >
                          Badge Primario
                        </span>
                        <span 
                          className="preview-badge"
                          style={{ backgroundColor: formData.accent_color + '20', color: formData.accent_color }}
                        >
                          Badge Acento
                        </span>
                      </div>
                    </div>

                    {/* Footer Preview */}
                    {formData.footer_text && (
                      <div className="preview-footer">
                        <p>{formData.footer_text}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="preview-placeholder">
                    <svg width="64" height="64" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                      <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                    </svg>
                    <p>Haga clic en "Ver Previa" para ver los cambios</p>
                  </div>
                )}
              </div>

              {/* Color Palette */}
              <div className="color-palette">
                <h4>Paleta de Colores</h4>
                <div className="palette-swatches">
                  <div className="swatch">
                    <div 
                      className="swatch-color" 
                      style={{ backgroundColor: formData.primary_color }}
                    ></div>
                    <span>Primario</span>
                  </div>
                  <div className="swatch">
                    <div 
                      className="swatch-color" 
                      style={{ backgroundColor: formData.secondary_color }}
                    ></div>
                    <span>Secundario</span>
                  </div>
                  <div className="swatch">
                    <div 
                      className="swatch-color" 
                      style={{ backgroundColor: formData.accent_color }}
                    ></div>
                    <span>Acento</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default ThemeEditor;
