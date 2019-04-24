import json
import os
import sys

from environ import Env

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = Env(
    ALLOWED_HOSTS=(str, ''),
    DEBUG=(bool, False),
    DEBUG_LEVEL=(str, 'INFO'),
)

ENV_FILE = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_FILE):
    Env.read_env(ENV_FILE)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '(%0hafx7+lsw4m6n(t)h!#sje$n$er9&z4hrfewm%&64=4mhy9'

DEBUG = env('DEBUG')

# Please use this to Enable/Disable the Admin site
ADMIN_ENABLED = True

ALLOWED_HOSTS = json.loads(env('ALLOWED_HOSTS')) if env('ALLOWED_HOSTS') else []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'applications.apps.ApplicationsConfig',
    'organisations.apps.OrganisationsConfig',
    'users.apps.UsersConfig',
    'cases.apps.CasesConfig',
    'queues.apps.QueuesConfig',
    'drafts.apps.DraftsConfig',
    'goods.apps.GoodsConfig',
    'reversion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'conf.urls'

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

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_AUTHENTICATION_CLASSES': (
    ),
    'DEFAULT_PERMISSION_CLASSES': (
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 4,
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

WSGI_APPLICATION = 'conf.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

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

# Static files (CSS, JavaScript, Images) for Django-Admin
STATIC_URL = '/static/'


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '(asctime)(levelname)(message)(filename)(lineno)(threadName)(name)(thread)(created)(process)(processName)(relativeCreated)(module)(funcName)(levelno)(msecs)(pathname)',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': env('DEBUG_LEVEL').upper(),
        },
    }
}
