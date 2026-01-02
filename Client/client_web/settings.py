"""
Django settings for client_web project.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings 
SECRET_KEY = 'django-insecure-#(yf^x)pz4mh@qfma&4!g&haiyimk+wswkt6*181k3vj(r4h2r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost'] # Added localhost for clarity


# Application definition

INSTALLED_APPS = [
    # Django Built-in Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom Client Application
   'client_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'client_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Project-level templates (e.g., base.html)
        'APP_DIRS': True, # Allows Django to find templates inside client_app/templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processor for media URL visibility in all templates
                'django.template.context_processors.media', 
            ],
        },
    },
]

WSGI_APPLICATION = 'client_web.wsgi.application'


# Database (Used for sessions, auth, and client-side functionality)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# (AUTH_PASSWORD_VALIDATORS remain default)


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# Optional: Define static root for production serving (not needed for development)
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 


# 🚀 MEDIA CONFIGURATION (CRITICAL FOR UPLOADED IMAGES) 🚀
# 1. MEDIA_ROOT: Defines the file system path where uploaded files (book covers) are stored.
# This points to the new 'media' folder you created at the project root level.
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# 2. MEDIA_URL: Defines the URL base used to access the uploaded files in the browser.
# e.g., files will be accessed via http://127.0.0.1:8000/media/...
MEDIA_URL = '/media/'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Authentication redirects
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
