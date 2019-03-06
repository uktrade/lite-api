import json
import os

import environ

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_FILE = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_FILE):
    environ.Env.read_env(ENV_FILE)

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(str, '')
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '(%0hafx7+lsw4m6n(t)h!#sje$n$er9&z4hrfewm%&64=4mhy9'

DEBUG = env('DEBUG')

ALLOWED_HOSTS = json.loads(env('ALLOWED_HOSTS')) if env('ALLOWED_HOSTS') else []

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',
    'drafts.apps.DraftsConfig',
    'applications.apps.ApplicationsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'conf.urls'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
      'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

WSGI_APPLICATION = 'conf.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

import sys
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'mydatabase'
        }
    }
else:
    DATABASES = {
        'default': env.db()
    }

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True
