import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.conf.settings")

app = Celery("api")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load celery_tasks.py modules from all registered Django apps.
app.autodiscover_tasks(related_name="celery_tasks")


BACKUP_DOCUMENT_DATA_SCHEDULE_NAME = "backup document data 2am"


# Define any regular scheduled tasks
app.conf.beat_schedule = {
    "update sanction search index at 7am, 7pm": {
        "task": "api.external_data.celery_tasks.update_sanction_search_index",
        "schedule": crontab(hour="7, 19", minute=0),
    },
    "update case SLAs 10.30pm": {
        "task": "api.cases.celery_tasks.update_cases_sla",
        "schedule": crontab(hour=22, minute=30),
    },
    BACKUP_DOCUMENT_DATA_SCHEDULE_NAME: {
        "task": "api.document_data.celery_tasks.backup_document_data",
        "schedule": crontab(hour=2, minute=0),
    },
    "send ecju query chaser emails 8pm, 4pm": {
        "task": "api.cases.celery_tasks.schedule_all_ecju_query_chaser_emails",
        "schedule": crontab(hour="8, 16", minute=0),
    },
}
