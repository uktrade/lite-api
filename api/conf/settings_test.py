from api.conf.settings import *


ELASTICSEARCH_SANCTION_INDEX_ALIAS = "sanctions-alias-test"

LOGGING = {"version": 1, "disable_existing_loggers": True}

SUPPRESS_TEST_OUTPUT = True

AWS_ENDPOINT_URL = None
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_STORE_EAGER_RESULT = True
