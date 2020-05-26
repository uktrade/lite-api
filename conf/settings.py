import json
import os
import sys

from environ import Env

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_FILE = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_FILE):
    Env.read_env(ENV_FILE)

env = Env(
    ALLOWED_HOSTS=(str, ""),
    DEBUG=(bool, False),
    LOG_LEVEL=(str, "INFO"),
    BACKGROUND_TASK_ENABLED=(bool, False),
    SUPPRESS_TEST_OUTPUT=(bool, False),
    HAWK_AUTHENTICATION_ENABLED=(bool, False),
    RECENTLY_UPDATED_WORKING_DAYS=(int, 5),
    STREAM_PAGE_SIZE=(int, 20),
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env("DEBUG")

# Please use this to Enable/Disable the Admin site
ADMIN_ENABLED = True

ALLOWED_HOSTS = json.loads(env("ALLOWED_HOSTS")) if env("ALLOWED_HOSTS") else []

# Application definition

INSTALLED_APPS = [
    "addresses",
    "applications.apps.ApplicationsConfig",
    "audit_trail",
    "background_task",
    "cases.app.CasesConfig",
    "cases.generated_documents",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "drf_yasg",
    "documents",
    "flags",
    "goods",
    "goodstype",
    "gov_users",
    "letter_templates",
    "licences",
    "organisations",
    "parties",
    "picklists",
    "queries",
    "queries.goods_query",
    "queries.end_user_advisories",
    "queues",
    "rest_framework",
    "static",
    "static.case_types",
    "static.control_list_entries",
    "static.countries",
    "static.decisions",
    "static.denial_reasons",
    "static.f680_clearance_types",
    "static.letter_layouts",
    "static.private_venture_gradings",
    "static.statuses",
    "static.trade_control",
    "static.units",
    "static.upload_document_for_tests",
    "teams",
    "users",
    "workflow.routing_rules",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "conf.middleware.LoggingMiddleware",
    "conf.middleware.DBLoggingMiddleware",
    "conf.middleware.HawkSigningMiddleware",
]

ROOT_URLCONF = "conf.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

AUTH_USER_MODEL = "users.BaseUser"

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_AUTHENTICATION_CLASSES": (),
    "DEFAULT_PERMISSION_CLASSES": (),
    "DEFAULT_PARSER_CLASSES": ("rest_framework.parsers.JSONParser", "rest_framework.parsers.FormParser"),
    "DEFAULT_PAGINATION_CLASS": "conf.pagination.MaxPageNumberPagination",
    "PAGE_SIZE": 25,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "EXCEPTION_HANDLER": "conf.handlers.lite_exception_handler",
}

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

SHA_ALGORITHM = "sha256"

HAWK_CREDENTIALS = {
    "exporter-frontend": {"id": "exporter-frontend", "key": env("LITE_EXPORTER_HAWK_KEY"), "algorithm": SHA_ALGORITHM},
    "internal-frontend": {"id": "internal-frontend", "key": env("LITE_INTERNAL_HAWK_KEY"), "algorithm": SHA_ALGORITHM},
    "hmrc-integration": {
        "id": "hmrc-integration",
        "key": env("LITE_HMRC_INTEGRATION_HAWK_KEY"),
        "algorithm": SHA_ALGORITHM,
    },
    "activity-stream": {
        "id": "activity-stream",
        "key": env("LITE_ACTIVITY_STREAM_HAWK_KEY"),
        "algorithm": SHA_ALGORITHM,
    },
    "lite-e2e": {"id": "lite-e2e", "key": env("LITE_E2E_HAWK_KEY"), "algorithm": SHA_ALGORITHM},
    "lite-performance": {"id": "lite-performance", "key": env("LITE_PERFORMANCE_HAWK_KEY"), "algorithm": SHA_ALGORITHM},
}

HAWK_AUTHENTICATION_ENABLED = env("HAWK_AUTHENTICATION_ENABLED")
HAWK_RECEIVER_NONCE_EXPIRY_SECONDS = 60

WSGI_APPLICATION = "conf.wsgi.application"

SWAGGER_SETTINGS = {"DEFAULT_INFO": "conf.urls.api_info"}

TEST_RUNNER = "xmlrunner.extra.djangotestrunner.XMLTestRunner"
TEST_OUTPUT_DIR = "test-results/unittest/"

STATIC_URL = "/assets/"

# CSS
STATIC_ROOT = os.path.join(BASE_DIR, "assets")
CSS_ROOT = os.path.join(STATIC_ROOT, "css")

LETTER_TEMPLATES_DIRECTORY = os.path.join(BASE_DIR, "letter_templates", "layouts")

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {"default": env.db()}

# AWS
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_REGION = env("AWS_REGION")
S3_DOWNLOAD_LINK_EXPIRY_SECONDS = 180
STREAMING_CHUNK_SIZE = 8192

# AV
AV_SERVICE_URL = env("AV_SERVICE_URL")
AV_SERVICE_USERNAME = env("AV_SERVICE_USERNAME")
AV_SERVICE_PASSWORD = env("AV_SERVICE_PASSWORD")

REQUEST_TIMEOUT = 5  # Maximum time to wait for a request made to AWS or AV

# Background tasks
BACKGROUND_TASK_ENABLED = env("BACKGROUND_TASK_ENABLED")
BACKGROUND_TASK_RUN_ASYNC = True
MAX_RUN_TIME = 180  # Time a given task is locked by a thread. After which, another thread can execute it simultaneously
MAX_ATTEMPTS = 3  # How many times a task will be attempted should an unhandled exception occur

UPLOAD_DOCUMENT_ENDPOINT_ENABLED = env("UPLOAD_DOCUMENT_ENDPOINT_ENABLED")

# If True, print the length of time it takes to run each test
TIME_TESTS = True
SUPPRESS_TEST_OUTPUT = env("SUPPRESS_TEST_OUTPUT")

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

if "test" not in sys.argv:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "(asctime)(levelname)(message)(filename)(lineno)(threadName)(name)(thread)(created)(process)(processName)(relativeCreated)(module)(funcName)(levelno)(msecs)(pathname)",  # noqa
            }
        },
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
        "loggers": {"": {"handlers": ["console"], "level": env("LOG_LEVEL").upper()}},
    }
else:
    LOGGING = {"version": 1, "disable_existing_loggers": True}

RECENTLY_UPDATED_WORKING_DAYS = env(
    "RECENTLY_UPDATED_WORKING_DAYS"
)  # Days that must have passed until we indicate a case has not been updated recently

# Security settings

SECURE_BROWSER_XSS_FILTER = True

STREAM_PAGE_SIZE = env("STREAM_PAGE_SIZE")
