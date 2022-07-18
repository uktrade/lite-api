from celery import shared_task
from api.cases.models import Case


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
