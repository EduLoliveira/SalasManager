from pathlib import Path
from decouple import config, Csv
import os
import secrets
import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = config(
    'SECRET_KEY',
    default=secrets.token_urlsafe(50)
)

DEBUG = config(
    'DEBUG',
    default=False,
    cast=bool
)


# =========================================================
# ALLOWED HOSTS
# =========================================================

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=Csv()
)

if '.onrender.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.onrender.com')

if 'salasmanager.onrender.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('salasmanager.onrender.com')


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'sales',
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =========================================================
# URL / WSGI
# =========================================================

ROOT_URLCONF = 'sistema_vendas.urls'

WSGI_APPLICATION = 'sistema_vendas.wsgi.application'


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
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


# =========================================================
# DATABASE
# Render + Supabase PostgreSQL
# =========================================================

DATABASE_URL = config(
    'DATABASE_URL',
    default='sqlite:///db.sqlite3'
)

if DATABASE_URL.startswith('postgres'):
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# =========================================================
# CUSTOM USER MODEL
# =========================================================

AUTH_USER_MODEL = 'sales.UsuarioCustomizado'


# =========================================================
# LOGIN / LOGOUT
# =========================================================

LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =========================================================
# AUTHENTICATION
# =========================================================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


# =========================================================
# E-MAIL
# =========================================================

if DEBUG:

    EMAIL_BACKEND = (
        'django.core.mail.backends.console.EmailBackend'
    )

else:

    EMAIL_BACKEND = (
        'django.core.mail.backends.smtp.EmailBackend'
    )

    EMAIL_HOST = config(
        'EMAIL_HOST',
        default='smtp.gmail.com'
    )

    EMAIL_PORT = config(
        'EMAIL_PORT',
        default=587,
        cast=int
    )

    EMAIL_USE_TLS = config(
        'EMAIL_USE_TLS',
        default=True,
        cast=bool
    )

    EMAIL_HOST_USER = config(
        'EMAIL_HOST_USER',
        default=''
    )

    EMAIL_HOST_PASSWORD = config(
        'EMAIL_HOST_PASSWORD',
        default=''
    )

    DEFAULT_FROM_EMAIL = config(
        'DEFAULT_FROM_EMAIL',
        default=EMAIL_HOST_USER
    )


# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True
USE_TZ = True


# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATIC_ROOT = os.path.join(
    BASE_DIR,
    'staticfiles'
)

STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)


# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =========================================================
# SESSION
# =========================================================

SESSION_COOKIE_AGE = 2409600

SESSION_SAVE_EVERY_REQUEST = True

SESSION_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_HTTPONLY = True


# =========================================================
# CSRF
# =========================================================

CSRF_TRUSTED_ORIGINS = [
    'https://salasmanager.onrender.com',
    'https://*.onrender.com',

    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

CSRF_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_HTTPONLY = True

CSRF_USE_SESSIONS = False


# =========================================================
# RENDER / HTTPS
# =========================================================

SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https'
)


# =========================================================
# SECURITY HEADERS
# =========================================================

if not DEBUG:

    SECURE_SSL_REDIRECT = True

    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True


# =========================================================
# WHITE NOISE
# =========================================================

WHITENOISE_USE_FINDERS = True
