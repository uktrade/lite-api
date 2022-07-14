from celery import shared_task


@shared_task
def debug_add(x, y):
    """
    Simple debug celery task to add two numbers.
    """
    return x + y
