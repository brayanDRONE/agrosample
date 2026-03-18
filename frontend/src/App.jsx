/**
 * Componente principal de la aplicación
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';
import AdminDashboard from './components/admin/AdminDashboard';
import EstablishmentManagement from './components/admin/EstablishmentManagement';
import ThemeEditor from './components/admin/ThemeEditor';
import InspectionApp from './components/InspectionApp';
import LandingPage from './pages/LandingPage';
import MaintenanceMode from './components/MaintenanceMode';
import './App.css';

// 🔧 FLAG DE MANTENIMIENTO - Cambiar a false para habilitar la aplicación
const MAINTENANCE_MODE = false;

function AppRoutes() {
  const { user, isSuperAdmin } = useAuth();

  // Si está en modo de mantenimiento, mostrar solo esa página
  if (MAINTENANCE_MODE) {
    return (
      <Routes>
        <Route path="*" element={<MaintenanceMode />} />
      </Routes>
    );
  }

  return (
    <Routes>
      {/* Ruta pública - Login */}
      <Route 
        path="/login" 
        element={
          user ? (
            <Navigate to={isSuperAdmin() ? '/admin' : '/'} replace />
          ) : (
            <Login />
          )
        } 
      />

      {/* Rutas de administrador */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute requireSuperAdmin={true}>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/establishments"
        element={
          <ProtectedRoute requireSuperAdmin={true}>
            <EstablishmentManagement />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/themes/:establishmentId"
        element={
          <ProtectedRoute requireSuperAdmin={true}>
            <ThemeEditor />
          </ProtectedRoute>
        }
      />

      {/* Ruta pública para la aplicación de inspección */}
      <Route
        path="/muestreo"
        element={<InspectionApp />}
      />

      {/* Ruta raíz - mostrar LandingPage */}
      <Route
        path="/"
        element={<LandingPage />}
      />

      {/* Redirección por defecto */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
