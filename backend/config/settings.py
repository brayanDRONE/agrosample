"""
Django settings for USDA Inspection System.
"""

from pathlib import Path
import os
import dj_database_url


def env_csv(var_name, default_csv):
    """Lee una variable CSV de entorno y elimina valores vacios/espacios."""
    raw = os.environ.get(var_name)
    source = raw if raw is not None else default_csv
    values = [item.strip() for item in source.split(',') if item.strip()]
    return values


def add_unique(items, value):
    """Agrega valor si no existe, preservando orden."""
    if value and value not in items:
        items.append(value)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: don't run with debug turned on in production!
is_hosted = os.environ.get('RENDER') == 'true' or bool(os.environ.get('RAILWAY_ENVIRONMENT'))
DEBUG = os.environ.get('DEBUG', 'False' if is_hosted else 'True') == 'True'
if is_hosted and DEBUG:
    raise RuntimeError('DEBUG no puede estar habilitado en el entorno alojado.')

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError('SECRET_KEY debe configurarse cuando DEBUG=False.')
    SECRET_KEY = 'django-insecure-local-dev-key-change-in-production'
if not DEBUG and SECRET_KEY == 'django-insecure-local-dev-key-change-in-production':
    raise RuntimeError('SECRET_KEY de desarrollo no se permite cuando DEBUG=False.')

ALLOWED_HOSTS = env_csv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
render_external_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip()
add_unique(ALLOWED_HOSTS, render_external_hostname)

# CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = env_csv('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173' if DEBUG else '')
if render_external_hostname:
    add_unique(CSRF_TRUSTED_ORIGINS, f'https://{render_external_hostname}')

# Reconocer el proxy (ej. Render) para generar URLs con https en lugar de http
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    
    # Local apps
    'inspections',
    'cherry_china_validation.apps.CherryChinaValidationConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Whitenoise for static files in production
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if os.environ.get('DATABASE_URL'):
    # Production: Use PostgreSQL from Render/Railway
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif not DEBUG:
    raise RuntimeError(
        'DATABASE_URL no está configurada para producción. '
        'Crea la base de datos PostgreSQL y conecta la variable DATABASE_URL '
        'al servicio del backend antes del deploy.'
    )
else:
    # Development: Use SQLite only for local environments.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

if not DEBUG and DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise RuntimeError('Producción requiere una base de datos PostgreSQL.')


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise configuration for production (Django 4.2+)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT', BASE_DIR / 'media'))

# Public landing-page contact form email delivery.
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '').strip()
RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', '').strip()
CONTACT_RECIPIENT_EMAIL = os.environ.get('CONTACT_RECIPIENT_EMAIL', '').strip()

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=8),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'CHECK_REVOKE_TOKEN': True,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = env_csv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://localhost:5177' if DEBUG else ''
)

# Mantener permitidos los dominios oficiales aunque la variable de Render no los incluya.
add_unique(CORS_ALLOWED_ORIGINS, 'https://agrosample.cl')
add_unique(CORS_ALLOWED_ORIGINS, 'https://www.agrosample.cl')

# Frontend URL opcional para producción (ej: https://mi-frontend.onrender.com)
frontend_url = os.environ.get('FRONTEND_URL', '').strip()
add_unique(CORS_ALLOWED_ORIGINS, frontend_url)

CORS_ALLOW_CREDENTIALS = True
