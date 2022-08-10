from celery import shared_task
from api.cases.models import Case

from django.conf import settings
from notifications_python_client import NotificationsAPIClient


@shared_task
def debug_add(x, y):
    """
    Simple debug celery task to add two numbers.
    """
    return x + y


@shared_task
def debug_count_cases():
    """
    Simple debug celery task to count the number of cases in the app.
    """
    return Case.objects.count()


@shared_task
def debug_exception():
    """
    Debug task which raises an exception.
    """
    raise Exception("debug_exception task")


@shared_task
def send_email(email_address, template_id, data):
    return NotificationsAPIClient(settings.GOV_NOTIFY_KEY).send_email_notification(
        email_address=email_address, template_id=template_id, personalisation=data
    )
