from api.conf.settings import *


ELASTICSEARCH_SANCTION_INDEX_ALIAS = "sanctions-alias-test"

LOGGING = {"version": 1, "disable_existing_loggers": True}

SUPPRESS_TEST_OUTPUT = True

AWS_ENDPOINT_URL = None

INSTALLED_APPS += [
    "api.core.tests.apps.CoreTestsConfig",
]


DB_ANONYMISER_AWS_ACCESS_KEY_ID = "fakekey"
DB_ANONYMISER_AWS_SECRET_ACCESS_KEY = "fakesecret"
DB_ANONYMISER_AWS_REGION = "eu-west-2"
DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME = "anonymiser-bucket"
DB_ANONYMISER_AWS_ENDPOINT_URL = None
