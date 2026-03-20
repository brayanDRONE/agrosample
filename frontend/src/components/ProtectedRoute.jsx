/**
 * ProtectedRoute - Componente para proteger rutas que requieren autenticación
 */

import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import SubscriptionExpiredView from './SubscriptionExpiredView';

function ProtectedRoute({ children, requireSuperAdmin = false, requireEstablishmentAdmin = false }) {
  const { user, loading, isSuperAdmin, isEstablishmentAdmin } = useAuth();

  // Mostrar loading mientras se verifica la autenticación
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        fontSize: '18px',
        color: '#718096'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{
            display: 'inline-block',
            width: '40px',
            height: '40px',
            border: '4px solid rgba(102, 126, 234, 0.2)',
            borderTopColor: '#667eea',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite'
          }}></div>
          <p style={{ marginTop: '20px' }}>Verificando autenticación...</p>
        </div>
      </div>
    );
  }

  // Si no hay usuario, redirigir a la portada pública
  if (!user) {
    return <Navigate to="/" replace />;
  }

  // Bloquear acceso si la suscripción del establecimiento está expirada o suspendida
  // Los superadmins nunca son bloqueados por suscripción
  const isEstAdmin = user?.role === 'ESTABLISHMENT_ADMIN' || user?.is_establishment_admin === true;
  const hasActiveSubscription = user?.establishment?.has_active_subscription !== false;
  if (isEstAdmin && !hasActiveSubscription) {
    return <SubscriptionExpiredView />;
  }

  // Verificar permisos según el tipo de ruta
  if (requireSuperAdmin && !isSuperAdmin()) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '20px'
      }}>
        <div style={{
          background: '#fed7d7',
          color: '#c53030',
          padding: '20px 30px',
          borderRadius: '8px',
          textAlign: 'center',
          maxWidth: '400px'
        }}>
          <h2 style={{ margin: '0 0 10px' }}>Acceso Denegado</h2>
          <p style={{ margin: 0 }}>No tiene permisos de superadministrador para acceder a esta sección.</p>
        </div>
      </div>
    );
  }

  if (requireEstablishmentAdmin && !isEstablishmentAdmin() && !isSuperAdmin()) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '20px'
      }}>
        <div style={{
          background: '#fed7d7',
          color: '#c53030',
          padding: '20px 30px',
          borderRadius: '8px',
          textAlign: 'center',
          maxWidth: '400px'
        }}>
          <h2 style={{ margin: '0 0 10px' }}>Acceso Denegado</h2>
          <p style={{ margin: 0 }}>No tiene permisos de administrador para acceder a esta sección.</p>
        </div>
      </div>
    );
  }

  // Si todas las verificaciones pasan, renderizar el componente hijo
  return children;
}

export default ProtectedRoute;
