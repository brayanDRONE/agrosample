# Sistema de Inspecciones SAG-USDA - Panel de Administración

## 🚀 Descripción General

Sistema multi-tenant para gestión de inspecciones y muestreo agrícola con panel de administración completo, control de suscripciones y personalización de interfaces por establecimiento.

## 👥 Roles de Usuario

### 1. **SUPERADMIN** (Administrador del Sistema)
- Acceso completo al panel administrativo
- Gestión de todos los establecimientos
- Control de suscripciones
- Personalización de temas
- Creación de usuarios administradores

### 2. **ESTABLISHMENT_ADMIN** (Administrador de Establecimiento)
- Acceso a la interfaz de inspección
- Gestión de datos del propio establecimiento
- Visualización personalizada según tema configurado

### 3. **INSPECTOR** (Usuario Inspector)
- Acceso solo a formularios de inspección
- Generación de muestras

## 🔐 Credenciales de Acceso

No se crean credenciales predeterminadas en instalaciones nuevas. Para crear
un superadministrador, seguir [la guía de despliegue](./DEPLOYMENT.md). Las
cuentas existentes conservan sus contraseñas: cambiar de forma segura cualquier
contraseña histórica o de prueba antes de usar el sistema en producción.
Al actualizar una contraseña, las sesiones anteriores dejan de ser válidas.

## 📊 Funcionalidades del Panel de Administración

### Dashboard Principal (`/admin`)
El dashboard muestra:
- **Total de Establecimientos**: Contador general
- **Activos**: Establecimientos con suscripción vigente
- **Por Vencer**: Establecimientos que vencen en los próximos 7 días
- **Expirados**: Establecimientos con suscripción vencida
- **Total Inspecciones**: Contador de inspecciones registradas
- **Actividad Reciente**: Últimas 10 inspecciones creadas

### Gestión de Establecimientos (`/admin/establishments`)

#### Ver Establecimientos
- Vista de tabla con todos los establecimientos
- Filtros rápidos: Todos / Activos / Por Vencer / Expirados
- Información visible por establecimiento:
  - Nombre y license key
  - RUT, email, teléfono
  - Estado de suscripción (badge con color)
  - Días hasta vencimiento

#### Crear Nuevo Establecimiento
1. Click en "**+ Nuevo Establecimiento**"
2. Completar formulario:
   - **Datos del Establecimiento**: Nombre*, RUT, Dirección, Teléfono, Email, Días de Suscripción*
   - **Datos del Administrador**: Usuario*, Email, Contraseña*
3. El sistema automáticamente:
   - Genera license key único (UUID)
   - Crea usuario administrador con perfil
   - Crea tema por defecto
   - Calcula fecha de expiración

#### Editar Establecimiento
- Click en botón **✏️ (Editar)**
- Permite modificar:
  - Nombre del establecimiento
  - RUT, dirección, teléfono, email
- No modifica suscripción ni usuario administrador

#### Renovar Suscripción
- Click en botón **🔄 (Renovar)**
- Especificar días a agregar (default: 30)
- Actualiza fecha de expiración
- Reactiva automáticamente si estaba expirado

#### Suspender/Activar
- **Suspender**: Bloquea acceso temporalmente (mantiene datos)
- **Activar**: Restaura acceso

#### Eliminar
- Elimina establecimiento, usuarios asociados, inspecciones y temas
- ⚠️ **Acción irreversible** - solicita confirmación

### Editor de Temas (`/admin/themes/:establishmentId`)

#### Personalización de Colores
Configura la paleta de colores del establecimiento:
- **Color Primario**: Color principal de la interfaz (botones, headers)
- **Color Secundario**: Color de gradientes y acentos
- **Color de Acento**: Color de alertas y elementos destacados

Cada color se puede:
- Seleccionar con selector visual (color picker)
- Ingresar código hexadecimal manualmente
- Ver en vista previa en tiempo real

#### Configuración de Marca
- **Nombre de la Compañía**: Reemplaza título por defecto
- **Mensaje de Bienvenida**: Texto personalizado en header
- **Texto del Footer**: Copyright o información adicional

#### Opciones de Visualización
- **Mostrar logo**: Toggle para mostrar/ocultar logo
- **Modo oscuro**: Modo experimental de tema oscuro

#### Vista Previa
- Click en "**Ver Previa**" para activar
- Visualización en tiempo real de cambios
- Muestra header, tarjetas, botones y badges con colores aplicados
- Paleta de colores con swatches visuales

## 🎨 Sistema de Temas Dinámicos

### Cómo Funciona
1. Al iniciar sesión, el sistema carga el tema del establecimiento del usuario
2. Los colores se aplican como variables CSS globales:
   - `--theme-primary`
   - `--theme-secondary`
   - `--theme-accent`
   - `--theme-gradient`
3. Los componentes usan estas variables automáticamente
4. El header muestra el nombre personalizado y mensaje de bienvenida

### Variables CSS Disponibles
```css
var(--theme-primary)         /* Color primario */
var(--theme-secondary)       /* Color secundario */
var(--theme-accent)          /* Color de acento */
var(--theme-gradient)        /* Gradiente principal */
var(--theme-primary-rgb)     /* RGB para transparencias */
```

## 🔄 Flujo de Trabajo Típico

### 1. Crear Nuevo Establecimiento
```
Login como admin → Dashboard → "+ Nuevo Establecimiento" → 
Completar formulario → Crear → Sistema genera todo automáticamente
```

### 2. Personalizar Interfaz
```
Dashboard → Ver Todos los Establecimientos → Click en 🎨 (Personalizar Tema) →
Configurar colores y marca → Ver Previa → Guardar Cambios
```

### 3. Renovar Suscripción Próxima a Vencer
```
Dashboard → Click en "Por Vencer (7 días)" → Seleccionar establecimiento →
Click en 🔄 (Renovar) → Ingresar días → Renovar
```

### 4. Suspender Establecimiento Temporalmente
```
Gestión de Establecimientos → Localizar establecimiento →
Click en ⛔ (Suspender) → Confirmar
```

## 📱 Rutas del Sistema

### Rutas Públicas
- `/login` - Página de inicio de sesión

### Rutas de Administrador (requiere rol SUPERADMIN)
- `/admin` - Dashboard administrativo
- `/admin/establishments` - Gestión de establecimientos
- `/admin/establishments/new` - Crear establecimiento (modal)
- `/admin/themes/:establishmentId` - Editor de temas

### Rutas de Usuario
- `/` - Interfaz de inspección (para ESTABLISHMENT_ADMIN e INSPECTOR)

## 🔧 Iniciar el Sistema

### Backend (Django)
```bash
cd c:\proyecto_usda\backend
python manage.py runserver
```
Servidor en: `http://localhost:8000`

### Frontend (React + Vite)
```bash
cd c:\proyecto_usda\frontend
npm run dev
```
Servidor en: `http://localhost:5173`

## 📝 Notas Importantes

1. **Autenticación JWT**: 
   - Access token: 60 minutos de duración
   - Refresh token: 24 horas
   - Auto-refresh automático cuando expira

2. **Suscripciones**:
   - Estado ACTIVE: Puede usar el sistema
   - Estado EXPIRED: Bloqueado, puede renovarse
   - Estado SUSPENDED: Bloqueado temporalmente por admin
   - "Por vencer": Menos de 7 días hasta expiración

3. **Temas**:
   - Se crean automáticamente al crear establecimiento
   - Se aplican dinámicamente sin recargar página
   - Colores en formato hexadecimal (#RRGGBB)
   - Vista previa no afecta otros usuarios

4. **Permisos**:
   - SUPERADMIN puede ver y editar todo
   - ESTABLISHMENT_ADMIN solo ve su propia interfaz personalizada
   - INSPECTOR solo accede a formularios

5. **Filtros de Establecimiento**:
   - Active: `has_active_subscription() == True`
   - Expiring Soon: `days_until_expiry < 7`
   - Expired: `subscription_status == 'EXPIRED'`

## 🐛 Solución de Problemas

### Error: "No autorizado" al acceder a rutas admin
- Verificar que esté logueado como usuario con rol SUPERADMIN
- Revisar token en localStorage: `localStorage.getItem('access_token')`

### Tema no se aplica
- Verificar que el establecimiento tenga tema creado
- Abrir consola del navegador y buscar errores
- El ThemeContext se carga automáticamente en InspectionApp

### No se pueden crear establecimientos
- Verificar que el usuario admin_username no exista
- Todos los campos marcados con * son obligatorios
- Contraseña debe tener al menos 1 carácter

## 📚 Estructura del Proyecto

```
proyecto_usda/
├── backend/
│   ├── inspections/
│   │   ├── models.py           # Establishment, EstablishmentTheme, UserProfile
│   │   ├── serializers_admin.py # Serializers para Admin API
│   │   ├── views_admin.py      # ViewSets de administración
│   │   └── urls.py             # Rutas API
│   └── manage.py
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── admin/
    │   │   │   ├── AdminDashboard.jsx         # Dashboard principal
    │   │   │   ├── EstablishmentManagement.jsx # CRUD establecimientos
    │   │   │   └── ThemeEditor.jsx            # Editor de temas
    │   │   ├── Login.jsx                      # Página de login
    │   │   ├── ProtectedRoute.jsx             # Guard de autenticación
    │   │   ├── InspectionApp.jsx              # App principal de inspección
    │   │   └── Header.jsx                     # Header dinámico
    │   ├── contexts/
    │   │   ├── AuthContext.jsx                # Estado de autenticación
    │   │   └── ThemeContext.jsx               # Estado de temas
    │   ├── services/
    │   │   └── api.js                         # Cliente API con interceptors
    │   ├── theme.css                          # Variables CSS globales
    │   └── App.jsx                            # Router principal
    └── package.json
```

## ✅ Checklist de Implementación

- [x] Sistema de autenticación JWT
- [x] Roles de usuario (SUPERADMIN, ESTABLISHMENT_ADMIN, INSPECTOR)
- [x] Dashboard administrativo con estadísticas
- [x] Gestión completa de establecimientos (CRUD)
- [x] Control de suscripciones (renovar, suspender, activar)
- [x] Editor de temas con vista previa
- [x] Sistema de temas dinámicos
- [x] Rutas protegidas por rol
- [x] Auto-refresh de tokens JWT
- [x] Interfaz responsive
- [x] Personalización por establecimiento

---

**Desarrollado para**: Sistema de Inspecciones SAG-USDA  
**Stack**: Django REST Framework + React + Vite  
**Autenticación**: JWT con Simple JWT  
**Arquitectura**: Multi-tenant con personalización por establecimiento
