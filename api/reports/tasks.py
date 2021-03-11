import logging

from background_task import background
from background_task.models import Task
from rest_framework import status


TASK_BACK_OFF = 3600  # Time, in seconds, to wait before scheduling a new task (used after MAX_ATTEMPTS is reached)

EMAIL_REPORTS_QUEUE = "email_reports_queue"
logger = logging.getLogger(__name__)


def email_reports():
    pass


@background(queue=EMAIL_REPORTS_QUEUE, schedule=0)
def email_reports_task():
    """Task that generates the reports and emails them"""

    logger.info("Polling inbox for updates")

    try:
        print("=====> Emailed reports")
        email_reports()
    except Exception as exc:  # noqa
        logging.error(f"An unexpected error occurred when emailing reports -> {type(exc).__name__}: {exc}")
        raise exc
