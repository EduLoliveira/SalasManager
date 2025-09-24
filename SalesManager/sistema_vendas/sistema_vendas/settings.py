from pathlib import Path
from decouple import config, Csv  
import os
import dj_database_url  

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# ← ADICIONE SEU DOMÍNIO DO RENDER AOS ALLOWED_HOSTS
ALLOWED_HOSTS += ['.onrender.com', 'salasManager.onrender.com']

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

ROOT_URLCONF = 'sistema_vendas.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'sistema_vendas.wsgi.application'

# ← DATABASE CONFIG COM FALLBACK (CORRIGIDO)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ← CONFIGURAÇÃO SEGURA PARA DATABASE_URL
# Use um valor padrão para evitar erro se DATABASE_URL não existir
database_url = config('DATABASE_URL', default='sqlite:///db.sqlite3')

if database_url and database_url != 'sqlite:///db.sqlite3':
    DATABASES['default'] = dj_database_url.config(
        default=database_url,
        conn_max_age=600,
        ssl_require=not DEBUG
    )

# Custom user model
AUTH_USER_MODEL = 'sales.UsuarioCustomizado'

# URLs de redirecionamento
LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Password validation
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

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Internationalization
LANGUAGE_CODE = 'pt-br' 
TIME_ZONE = 'America/Sao_Paulo'  
USE_I18N = True
USE_TZ = True

# Configuração de arquivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 2409600
SESSION_SAVE_EVERY_REQUEST = True

# Configurações CSRF para produção
CSRF_TRUSTED_ORIGINS = [
    'https://salasManager.onrender.com',
    'https://*.onrender.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

CSRF_COOKIE_SECURE = not DEBUG  # True em produção
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = False

# Configurações de sessão
SESSION_COOKIE_SECURE = not DEBUG  # True em produção
SESSION_COOKIE_HTTPONLY = True
