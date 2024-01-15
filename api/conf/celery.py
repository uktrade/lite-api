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
}
