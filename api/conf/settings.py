import logging
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

from environ import Env
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from dbt_copilot_python.network import setup_allowed_hosts
from dbt_copilot_python.database import database_url_from_env
from dbt_copilot_python.utility import is_copilot

import dj_database_url

from django_log_formatter_ecs import ECSFormatter
from django_log_formatter_asim import ASIMFormatter


from django.urls import reverse_lazy

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_FILE = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_FILE):
    Env.read_env(ENV_FILE)

env = Env(
    ALLOWED_HOSTS=(str, ""),
    DEBUG=(bool, False),
    LOG_LEVEL=(str, "INFO"),
    SUPPRESS_TEST_OUTPUT=(bool, False),
    HAWK_AUTHENTICATION_ENABLED=(bool, True),
    LITE_HMRC_INTEGRATION_ENABLED=(bool, False),
    RECENTLY_UPDATED_WORKING_DAYS=(int, 5),
    STREAM_PAGE_SIZE=(int, 20),
    ENV=(str, "localhost"),
    EXPORTER_BASE_URL=(str, ""),
    CASEWORKER_BASE_URL=(str, ""),
    GOV_NOTIFY_ENABLED=(bool, False),
    DOCUMENT_SIGNING_ENABLED=(bool, False),
    GIT_COMMIT=(str, ""),
    MOCK_VIRUS_SCAN_ACTIVATE_ENDPOINTS=(bool, False),
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env("DEBUG")

ENV = env("ENV")
VCAP_SERVICES = env.json("VCAP_SERVICES", {})

IS_ENV_DBT_PLATFORM = is_copilot()
IS_ENV_GOV_PAAS = bool(VCAP_SERVICES)

# Please use this to Enable/Disable the Admin site
ADMIN_ENABLED = env("ADMIN_ENABLED", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# django-allow-cidr
ALLOWED_CIDR_NETS = ["10.0.0.0/8"]

# Application definition
INSTALLED_APPS = [
    "api.addresses",
    "api.applications",
    "api.audit_trail",
    "api.bookmarks",
    "api.cases",
    "api.cases.generated_documents",
    "api.compliance",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "phonenumber_field",
    "api.core",
    "api.documents",
    "api.flags",
    "api.goods",
    "api.goodstype",  # this can't be removed yet as migrations need to be kept as dependencies
    "api.gov_users",
    "api.letter_templates",
    "api.licences",
    "api.organisations",
    "api.parties",
    "api.picklists",
    "api.queries",
    "api.queries.goods_query",
    "api.queries.end_user_advisories",
    "api.queues",
    "rest_framework",
    "api.staticdata",
    "api.staticdata.case_types",
    "api.staticdata.control_list_entries",
    "api.staticdata.countries",
    "api.staticdata.decisions",
    "api.staticdata.denial_reasons",
    "api.staticdata.f680_clearance_types",
    "api.staticdata.letter_layouts",
    "api.staticdata.private_venture_gradings",
    "api.staticdata.statuses",
    "api.staticdata.trade_control",
    "api.staticdata.units",
    "api.staticdata.upload_document_for_tests",
    "api.staticdata.regimes",
    "api.staticdata.report_summaries",
    "api.teams",
    "api.users",
    "api.workflow.routing_rules",
    "api.search",
    "api.search.application",
    "api.search.product",
    "api.data_workspace",
    "api.external_data",
    "api.support",
    "api.f680",
    "health_check",
    "health_check.cache",
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    "health_check.db",
    "health_check.contrib.migrations",
    "health_check.storage",
    "django_audit_log_middleware",
    "lite_routing",
    "api.appeals",
    "api.assessments",
    "api.document_data",
    "api.survey",
    "django_db_anonymiser.db_anonymiser",
    "reversion",
    "drf_spectacular",
]

MOCK_VIRUS_SCAN_ACTIVATE_ENDPOINTS = env("MOCK_VIRUS_SCAN_ACTIVATE_ENDPOINTS")

if MOCK_VIRUS_SCAN_ACTIVATE_ENDPOINTS:
    INSTALLED_APPS += [
        "mock_virus_scan",
    ]


MIDDLEWARE = [
    "allow_cidr.middleware.AllowCIDRMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "reversion.middleware.RevisionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "api.conf.middleware.HawkSigningMiddleware",
    "django_audit_log_middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "api.conf.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR + "/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

AUTH_USER_MODEL = "users.BaseUser"


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_AUTHENTICATION_CLASSES": (),
    "DEFAULT_PERMISSION_CLASSES": (),
    "DEFAULT_METADATA_CLASS": "api.core.metadata.SimpleMetadataForAllMethods",
    "DEFAULT_PARSER_CLASSES": ("rest_framework.parsers.JSONParser", "rest_framework.parsers.FormParser"),
    "DEFAULT_PAGINATION_CLASS": "api.conf.pagination.MaxPageNumberPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": 25,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "EXCEPTION_HANDLER": "api.core.handlers.lite_exception_handler",
}

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

HAWK_AUTHENTICATION_ENABLED = env("HAWK_AUTHENTICATION_ENABLED")
HAWK_RECEIVER_NONCE_EXPIRY_SECONDS = 60
HAWK_ALGORITHM = "sha256"
HAWK_LITE_API_CREDENTIALS = "lite-api"
HAWK_LITE_PERFORMANCE_CREDENTIALS = "lite-performance"
HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS = "hmrc-integration"
HAWK_LITE_DATA_WORKSPACE_CREDENTIALS = "lite-data-workspace"
HAWK_CREDENTIALS = {
    "exporter-frontend": {"id": "exporter-frontend", "key": env("LITE_EXPORTER_HAWK_KEY"), "algorithm": HAWK_ALGORITHM},
    "internal-frontend": {"id": "internal-frontend", "key": env("LITE_INTERNAL_HAWK_KEY"), "algorithm": HAWK_ALGORITHM},
    "activity-stream": {
        "id": "activity-stream",
        "key": env("LITE_ACTIVITY_STREAM_HAWK_KEY"),
        "algorithm": HAWK_ALGORITHM,
    },
    HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS: {
        "id": HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
        "key": env("LITE_HMRC_INTEGRATION_HAWK_KEY"),
        "algorithm": HAWK_ALGORITHM,
    },
    "lite-e2e": {"id": "lite-e2e", "key": env("LITE_E2E_HAWK_KEY"), "algorithm": HAWK_ALGORITHM},
    HAWK_LITE_PERFORMANCE_CREDENTIALS: {
        "id": HAWK_LITE_PERFORMANCE_CREDENTIALS,
        "key": env("LITE_PERFORMANCE_HAWK_KEY"),
        "algorithm": HAWK_ALGORITHM,
    },
    HAWK_LITE_API_CREDENTIALS: {
        "id": HAWK_LITE_API_CREDENTIALS,
        "key": env("LITE_API_HAWK_KEY"),
        "algorithm": HAWK_ALGORITHM,
    },
    HAWK_LITE_DATA_WORKSPACE_CREDENTIALS: {
        "id": HAWK_LITE_DATA_WORKSPACE_CREDENTIALS,
        "key": env("HAWK_LITE_DATA_WORKSPACE_KEY"),
        "algorithm": HAWK_ALGORITHM,
    },
}

WSGI_APPLICATION = "api.conf.wsgi.application"

TEST_RUNNER = "xmlrunner.extra.djangotestrunner.XMLTestRunner"
TEST_OUTPUT_DIR = "test-results/unittest/"

STATIC_URL = "/assets/"

# CSS
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "assets")
CSS_ROOT = os.path.join(STATIC_ROOT, "css")

# Cache static files
STATICFILES_STORAGE = env.str("STATICFILES_STORAGE", "whitenoise.storage.CompressedManifestStaticFilesStorage")

LETTER_TEMPLATES_DIRECTORY = os.path.join(BASE_DIR, "letter_templates", "templates", "letter_templates")


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# AWS

S3_BUCKET_TAG_FILE_UPLOADS = "file-uploads"

CELERY_ALWAYS_EAGER = env.bool("CELERY_ALWAYS_EAGER", False)
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_STORE_EAGER_RESULT = env.bool("CELERY_TASK_STORE_EAGER_RESULT", False)
CELERY_TASK_SEND_SENT_EVENT = env.bool("CELERY_TASK_SEND_SENT_EVENT", True)
CELERY_TASK_TRACK_STARTED = env.bool("CELERY_TASK_TRACK_STARTED", True)


S3_CONNECT_TIMEOUT = 60  # Maximum time, in seconds, to wait for an initial connection
S3_REQUEST_TIMEOUT = 60  # Maximum time, in seconds, to wait between bytes of a response
S3_DOWNLOAD_LINK_EXPIRY_SECONDS = 180
STREAMING_CHUNK_SIZE = 8192

# AV
AV_SERVICE_URL = env("AV_SERVICE_URL")
AV_SERVICE_USERNAME = env("AV_SERVICE_USERNAME")
AV_SERVICE_PASSWORD = env("AV_SERVICE_PASSWORD")
AV_REQUEST_TIMEOUT = 60  # Maximum time, in seconds, to wait between bytes of a response

# HMRC Integration
LITE_HMRC_INTEGRATION_ENABLED = env("LITE_HMRC_INTEGRATION_ENABLED")
LITE_HMRC_INTEGRATION_URL = env("LITE_HMRC_INTEGRATION_URL")
LITE_HMRC_REQUEST_TIMEOUT = 60  # Maximum time, in seconds, to wait between bytes of a response

UPLOAD_DOCUMENT_ENDPOINT_ENABLED = env("UPLOAD_DOCUMENT_ENDPOINT_ENABLED")

TIME_TESTS = True  # If True, print the length of time it takes to run each test
SUPPRESS_TEST_OUTPUT = env("SUPPRESS_TEST_OUTPUT")

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "Europe/London"

USE_I18N = True

USE_L10N = True

USE_TZ = True

PHONENUMBER_DB_FORMAT = "E164"

ELASTICSEARCH_SANCTION_INDEX_ALIAS = env.str("ELASTICSEARCH_SANCTION_INDEX_ALIAS", "sanctions-alias")
ELASTICSEARCH_DENIALS_INDEX_ALIAS = env.str("ELASTICSEARCH_DENIALS_INDEX_ALIAS", "denials-alias")
ELASTICSEARCH_PRODUCT_INDEX_ALIAS = env.str("ELASTICSEARCH_PRODUCT_INDEX_ALIAS", "products-alias")
ELASTICSEARCH_APPLICATION_INDEX_ALIAS = env.str("ELASTICSEARCH_APPLICATION_INDEX_ALIAS", "application-alias")


DENIAL_REASONS_DELETION_LOGGER = "denial_reasons_deletion_logger"

# Sentry
if env.str("SENTRY_DSN", ""):
    sentry_sdk.init(
        dsn=env.str("SENTRY_DSN"),
        environment=env.str("SENTRY_ENVIRONMENT"),
        integrations=[DjangoIntegration()],
        send_default_pii=True,
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", 1.0),
    )

# Application Performance Monitoring
if env.str("ELASTIC_APM_SERVER_URL", ""):
    ELASTIC_APM = {
        "SERVICE_NAME": env.str("ELASTIC_APM_SERVICE_NAME", "lite-api"),
        "SECRET_TOKEN": env.str("ELASTIC_APM_SECRET_TOKEN"),
        "SERVER_URL": env.str("ELASTIC_APM_SERVER_URL"),
        "ENVIRONMENT": env.str("SENTRY_ENVIRONMENT"),
        "DEBUG": DEBUG,
    }
    INSTALLED_APPS.append("elasticapm.contrib.django")


RECENTLY_UPDATED_WORKING_DAYS = env(
    "RECENTLY_UPDATED_WORKING_DAYS"
)  # Days that must have passed until we indicate a case has not been updated recently

# Security settings

SECURE_BROWSER_XSS_FILTER = True

STREAM_PAGE_SIZE = env("STREAM_PAGE_SIZE")


GOV_NOTIFY_ENABLED = env("GOV_NOTIFY_ENABLED")

GOV_NOTIFY_KEY = env("GOV_NOTIFY_KEY")

# If EXPORTER_BASE_URL is not in env vars, build the base_url using the environment
EXPORTER_BASE_URL = env("EXPORTER_BASE_URL") or f"https://exporter.lite.service.{ENV}.uktrade.digital"

# If CASEWORKER_BASE_URL is not in env vars, build the base_url using the environment
CASEWORKER_BASE_URL = env("CASEWORKER_BASE_URL") or f"https://internal.lite.service.{ENV}.uktrade.digital"


# Document signing
DOCUMENT_SIGNING_ENABLED = env("DOCUMENT_SIGNING_ENABLED")
P12_CERTIFICATE = env("P12_CERTIFICATE")
CERTIFICATE_PASSWORD = env("CERTIFICATE_PASSWORD")
SIGNING_EMAIL = env("SIGNING_EMAIL")
SIGNING_LOCATION = env("SIGNING_LOCATION")
SIGNING_REASON = env("SIGNING_REASON")

# Django Extensions
if DEBUG and "django_extensions" in sys.modules:
    INSTALLED_APPS.append("django_extensions")

    GRAPH_MODELS = {
        "all_applications": False,
        "group_models": True,
    }


# SSO config
FEATURE_STAFF_SSO_ENABLED = env.bool("FEATURE_STAFF_SSO_ENABLED", False)
if FEATURE_STAFF_SSO_ENABLED and ADMIN_ENABLED:
    INSTALLED_APPS.append("authbroker_client")
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "authbroker_client.backends.AuthbrokerBackend",
    ]
    LOGIN_URL = reverse_lazy("authbroker_client:login")
    LOGIN_REDIRECT_URL = reverse_lazy("admin:index")
    AUTHBROKER_URL = env.str("STAFF_SSO_AUTHBROKER_URL")
    AUTHBROKER_CLIENT_ID = env.str("STAFF_SSO_AUTHBROKER_CLIENT_ID")
    AUTHBROKER_CLIENT_SECRET = env.str("STAFF_SSO_AUTHBROKER_CLIENT_SECRET")
    ALLOWED_ADMIN_EMAILS = env.list("ALLOWED_ADMIN_EMAILS")


PERMISSIONS_FINDER_URL = env.str("PERMISSIONS_FINDER_URL")

# Controls whether a ComplianceSiteCase is automatically created when a SIEL licence is issued that has goods with certain control codes
# See LTD-1159
FEATURE_SIEL_COMPLIANCE_ENABLED = env.bool("FEATURE_SIEL_COMPLIANCE_ENABLED", False)

FEATURE_C8_ROUTING_ENABLED = env.bool("FEATURE_C8_ROUTING_ENABLED", False)

SANCTION_LIST_SOURCES = env.json(
    "SANCTION_LIST_SOURCES",
    {
        "un_sanctions_file": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
        "office_financial_sanctions_file": "https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.xml",
        "uk_sanctions_file": "https://assets.publishing.service.gov.uk/media/679b8f9eabe77b74cc146c71/UK_Sanctions_List.xml",  # /PS-IGNORE
    },
)
LITE_INTERNAL_NOTIFICATION_EMAILS = env.json("LITE_INTERNAL_NOTIFICATION_EMAILS", {})

GIT_COMMIT_SHA = env.str("GIT_COMMIT", "UNKNOWN")
# Only extract the git commit sha by subprocess if we are running locally
if GIT_COMMIT_SHA == "UNKNOWN" and ENV == "local":
    import subprocess  # nosec

    try:
        GIT_COMMIT_SHA = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()  # nosec
    except Exception:
        GIT_COMMIT_SHA = "UNKNOWN"

ENABLE_DJANGO_SILK = env.bool("ENABLE_DJANGO_SILK", False)

if ENABLE_DJANGO_SILK:
    INSTALLED_APPS.append("silk")
    middleware_index = MIDDLEWARE.index("django.contrib.messages.middleware.MessageMiddleware") + 1
    MIDDLEWARE.insert(middleware_index, "silk.middleware.SilkyMiddleware")

if DEBUG:
    INSTALLED_APPS.append("api.testing")


CONTENT_DATA_MIGRATION_DIR = Path(BASE_DIR).parent / "lite_content/lite_api/migrations"

BACKUP_DOCUMENT_DATA_TO_DB = env("BACKUP_DOCUMENT_DATA_TO_DB", default=True)


S3_BUCKET_TAG_ANONYMISER_DESTINATION = "anonymiser"

ELASTICSEARCH_SANCTION_INDEX_ALIAS = env.str("ELASTICSEARCH_SANCTION_INDEX_ALIAS", "sanctions-alias")
ELASTICSEARCH_DENIALS_INDEX_ALIAS = env.str("ELASTICSEARCH_DENIALS_INDEX_ALIAS", "denials-alias")
ELASTICSEARCH_PRODUCT_INDEX_ALIAS = env.str("ELASTICSEARCH_PRODUCT_INDEX_ALIAS", "products-alias")
ELASTICSEARCH_APPLICATION_INDEX_ALIAS = env.str("ELASTICSEARCH_APPLICATION_INDEX_ALIAS", "application-alias")

DB_ANONYMISER_CONFIG_LOCATION = Path(BASE_DIR) / "conf" / "anonymise_model_config.yaml"
DB_ANONYMISER_DUMP_FILE_NAME = env.str("DB_ANONYMISER_DUMP_FILE_NAME", "anonymised.sql")


def _build_redis_url(base_url, db_number, **query_args):
    encoded_query_args = urlencode(query_args)
    return f"{base_url}/{db_number}?{encoded_query_args}"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "sentry": {"class": "sentry_sdk.integrations.logging.EventHandler"},
    },
    "loggers": {
        DENIAL_REASONS_DELETION_LOGGER: {"handlers": ["sentry"], "level": logging.WARNING},
    },
}

if IS_ENV_DBT_PLATFORM:
    ALLOWED_HOSTS = setup_allowed_hosts(ALLOWED_HOSTS)
    AWS_ENDPOINT_URL = env("AWS_ENDPOINT_URL", default=None)
    AWS_REGION = "eu-west-2"
    DATABASES = {"default": dj_database_url.config(default=database_url_from_env("DATABASE_CREDENTIALS"))}
    CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=None)
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL
    REDIS_BASE_URL = env("REDIS_BASE_URL", default=None)

    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    DB_ANONYMISER_AWS_ENDPOINT_URL = AWS_ENDPOINT_URL
    DB_ANONYMISER_AWS_ACCESS_KEY_ID = env("DB_ANONYMISER_AWS_ACCESS_KEY_ID", default=None)
    DB_ANONYMISER_AWS_SECRET_ACCESS_KEY = env("DB_ANONYMISER_AWS_SECRET_ACCESS_KEY", default=None)
    DB_ANONYMISER_AWS_REGION = env("DB_ANONYMISER_AWS_REGION", default=None)
    DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME = env("DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME", default=None)

    if REDIS_BASE_URL:
        # Give celery tasks their own redis DB - future uses of redis should use a different DB
        REDIS_CELERY_DB = env("REDIS_CELERY_DB", default=0)
        is_redis_ssl = REDIS_BASE_URL.startswith("rediss://")
        url_args = {"ssl_cert_reqs": "CERT_REQUIRED"} if is_redis_ssl else {}
        CELERY_BROKER_URL = _build_redis_url(REDIS_BASE_URL, REDIS_CELERY_DB, **url_args)
        CELERY_RESULT_BACKEND = CELERY_BROKER_URL

    # Elasticsearch configuration
    LITE_API_ENABLE_ES = env.bool("LITE_API_ENABLE_ES", False)
    if LITE_API_ENABLE_ES:
        ELASTICSEARCH_DSL = {
            "default": {
                "hosts": env.str("OPENSEARCH_ENDPOINT"),
                "timeout": 30,
            },
        }

        ENABLE_SPIRE_SEARCH = env.bool("ENABLE_SPIRE_SEARCH", False)

        ELASTICSEARCH_PRODUCT_INDEXES = {"LITE": ELASTICSEARCH_PRODUCT_INDEX_ALIAS}
        ELASTICSEARCH_APPLICATION_INDEXES = {"LITE": ELASTICSEARCH_APPLICATION_INDEX_ALIAS}
        SPIRE_APPLICATION_INDEX_NAME = env.str("SPIRE_APPLICATION_INDEX_NAME", "spire-application-alias")
        SPIRE_PRODUCT_INDEX_NAME = env.str("SPIRE_PRODUCT_INDEX_NAME", "spire-products-alias")

        if ENABLE_SPIRE_SEARCH:
            ELASTICSEARCH_APPLICATION_INDEXES["SPIRE"] = SPIRE_APPLICATION_INDEX_NAME
            ELASTICSEARCH_PRODUCT_INDEXES["SPIRE"] = SPIRE_PRODUCT_INDEX_NAME

        INSTALLED_APPS += [
            "django_elasticsearch_dsl",
            "django_elasticsearch_dsl_drf",
        ]

    LOGGING.update({"formatters": {"asim_formatter": {"()": ASIMFormatter}}})
    LOGGING["handlers"].update({"asim": {"class": "logging.StreamHandler", "formatter": "asim_formatter"}})
    LOGGING.update({"root": {"handlers": ["asim"], "level": env("LOG_LEVEL").upper()}})

elif IS_ENV_GOV_PAAS:
    # This has repeating code as this section can be deleted once migrated to DBT Platform
    # Database
    DATABASES = {"default": env.db()}  # https://docs.djangoproject.com/en/2.1/ref/settings/#databases
    # redis
    REDIS_BASE_URL = VCAP_SERVICES["redis"][0]["credentials"]["uri"]

    if REDIS_BASE_URL:
        # Give celery tasks their own redis DB - future uses of redis should use a different DB
        REDIS_CELERY_DB = env("REDIS_CELERY_DB", default=0)
        is_redis_ssl = REDIS_BASE_URL.startswith("rediss://")
        url_args = {"ssl_cert_reqs": "CERT_REQUIRED"} if is_redis_ssl else {}

        CELERY_BROKER_URL = _build_redis_url(REDIS_BASE_URL, REDIS_CELERY_DB, **url_args)
        CELERY_RESULT_BACKEND = CELERY_BROKER_URL

    # Elasticsearch configuration
    LITE_API_ENABLE_ES = env.bool("LITE_API_ENABLE_ES", False)
    if LITE_API_ENABLE_ES:
        ELASTICSEARCH_DSL = {
            "default": {"hosts": env.str("ELASTICSEARCH_HOST")},
        }

        ENABLE_SPIRE_SEARCH = env.bool("ENABLE_SPIRE_SEARCH", False)

        ELASTICSEARCH_PRODUCT_INDEXES = {"LITE": ELASTICSEARCH_PRODUCT_INDEX_ALIAS}
        ELASTICSEARCH_APPLICATION_INDEXES = {"LITE": ELASTICSEARCH_APPLICATION_INDEX_ALIAS}
        SPIRE_APPLICATION_INDEX_NAME = env.str("SPIRE_APPLICATION_INDEX_NAME", "spire-application-alias")
        SPIRE_PRODUCT_INDEX_NAME = env.str("SPIRE_PRODUCT_INDEX_NAME", "spire-products-alias")

        if ENABLE_SPIRE_SEARCH:
            ELASTICSEARCH_APPLICATION_INDEXES["SPIRE"] = SPIRE_APPLICATION_INDEX_NAME
            ELASTICSEARCH_PRODUCT_INDEXES["SPIRE"] = SPIRE_PRODUCT_INDEX_NAME

        INSTALLED_APPS += [
            "django_elasticsearch_dsl",
            "django_elasticsearch_dsl_drf",
        ]
    # AWS
    if "aws-s3-bucket" not in VCAP_SERVICES:
        raise Exception("S3 Bucket not bound to environment")

    for bucket_details in VCAP_SERVICES["aws-s3-bucket"]:
        if S3_BUCKET_TAG_FILE_UPLOADS in bucket_details["tags"]:
            aws_credentials = bucket_details["credentials"]
            AWS_ENDPOINT_URL = None
            AWS_ACCESS_KEY_ID = aws_credentials["aws_access_key_id"]
            AWS_SECRET_ACCESS_KEY = aws_credentials["aws_secret_access_key"]
            AWS_REGION = aws_credentials["aws_region"]
            AWS_STORAGE_BUCKET_NAME = aws_credentials["bucket_name"]

        if S3_BUCKET_TAG_ANONYMISER_DESTINATION in bucket_details["tags"]:
            aws_credentials = bucket_details["credentials"]
            DB_ANONYMISER_AWS_ENDPOINT_URL = None
            DB_ANONYMISER_AWS_ACCESS_KEY_ID = aws_credentials["aws_access_key_id"]
            DB_ANONYMISER_AWS_SECRET_ACCESS_KEY = aws_credentials["aws_secret_access_key"]
            DB_ANONYMISER_AWS_REGION = aws_credentials["aws_region"]
            DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME = aws_credentials["bucket_name"]

    LOGGING.update({"formatters": {"ecs_formatter": {"()": ECSFormatter}}})
    LOGGING["handlers"].update({"ecs": {"class": "logging.StreamHandler", "formatter": "ecs_formatter"}})
    LOGGING.update({"root": {"handlers": ["ecs"], "level": env("LOG_LEVEL").upper()}})

else:
    # Local configurations and CircleCI
    # Database
    DATABASES = {"default": env.db()}  # https://docs.djangoproject.com/en/2.1/ref/settings/#databases
    # redis
    REDIS_BASE_URL = env("REDIS_BASE_URL", default=None)

    if REDIS_BASE_URL:
        # Give celery tasks their own redis DB - future uses of redis should use a different DB
        REDIS_CELERY_DB = env("REDIS_CELERY_DB", default=0)
        is_redis_ssl = REDIS_BASE_URL.startswith("rediss://")
        url_args = {"ssl_cert_reqs": "CERT_REQUIRED"} if is_redis_ssl else {}

        CELERY_BROKER_URL = _build_redis_url(REDIS_BASE_URL, REDIS_CELERY_DB, **url_args)
        CELERY_RESULT_BACKEND = CELERY_BROKER_URL

    # Elasticsearch configuration
    LITE_API_ENABLE_ES = env.bool("LITE_API_ENABLE_ES", False)
    if LITE_API_ENABLE_ES:
        ELASTICSEARCH_DSL = {
            "default": {"hosts": env.str("ELASTICSEARCH_HOST")},
        }

        ENABLE_SPIRE_SEARCH = env.bool("ENABLE_SPIRE_SEARCH", False)

        ELASTICSEARCH_PRODUCT_INDEXES = {"LITE": ELASTICSEARCH_PRODUCT_INDEX_ALIAS}
        ELASTICSEARCH_APPLICATION_INDEXES = {"LITE": ELASTICSEARCH_APPLICATION_INDEX_ALIAS}
        SPIRE_APPLICATION_INDEX_NAME = env.str("SPIRE_APPLICATION_INDEX_NAME", "spire-application-alias")
        SPIRE_PRODUCT_INDEX_NAME = env.str("SPIRE_PRODUCT_INDEX_NAME", "spire-products-alias")

        if ENABLE_SPIRE_SEARCH:
            ELASTICSEARCH_APPLICATION_INDEXES["SPIRE"] = SPIRE_APPLICATION_INDEX_NAME
            ELASTICSEARCH_PRODUCT_INDEXES["SPIRE"] = SPIRE_PRODUCT_INDEX_NAME

        INSTALLED_APPS += [
            "django_elasticsearch_dsl",
            "django_elasticsearch_dsl_drf",
        ]
    # AWS
    AWS_ENDPOINT_URL = env("AWS_ENDPOINT_URL", default=None)
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = env("AWS_REGION")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")

    DB_ANONYMISER_AWS_ENDPOINT_URL = AWS_ENDPOINT_URL
    DB_ANONYMISER_AWS_ACCESS_KEY_ID = env("DB_ANONYMISER_AWS_ACCESS_KEY_ID", default=None)
    DB_ANONYMISER_AWS_SECRET_ACCESS_KEY = env("DB_ANONYMISER_AWS_SECRET_ACCESS_KEY", default=None)
    DB_ANONYMISER_AWS_REGION = env("DB_ANONYMISER_AWS_REGION", default=None)
    DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME = env("DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME", default=None)

    LOGGING.update({"formatters": {"simple": {"format": "{asctime} {levelname} {message}", "style": "{"}}})
    LOGGING["handlers"].update({"stdout": {"class": "logging.StreamHandler", "formatter": "simple"}})
    LOGGING.update({"root": {"handlers": ["stdout"], "level": env("LOG_LEVEL").upper()}})

ROUTING_DOCS_DIRECTORY = os.path.join(BASE_DIR, "..", "lite_routing", "docs")
