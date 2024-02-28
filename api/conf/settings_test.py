from api.conf.settings import *


ELASTICSEARCH_SANCTION_INDEX_ALIAS = "sanctions-alias-test"

LOGGING = {"version": 1, "disable_existing_loggers": True}

SUPPRESS_TEST_OUTPUT = True

AWS_ENDPOINT_URL = None

INSTALLED_APPS += [
    "api.core.tests.apps.CoreTestsConfig",
]
