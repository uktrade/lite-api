import logging
from datetime import timedelta

from background_task import background
from background_task.models import Task
from django.utils import timezone

from cases.libraries import hmrc_integration_operations
from conf.settings import MAX_ATTEMPTS
from licences.models import Licence

TASK_QUEUE = "hmrc_integration_queue"


@background(schedule=0, queue=TASK_QUEUE)
def send_licence_changes_to_hmrc_integration(licence_id):
    """
    Executed by background worker process or synchronous depending on BACKGROUND_TASK_RUN_ASYNC.
    """

    logging.info(f"Sending licence '{licence_id}' changes to HMRC Integration")

    try:
        licence = Licence.objects.get(id=licence_id)

        return hmrc_integration_operations.send_licence_changes(licence)
    except Licence.DoesNotExist as exc:
        logging.warning(str(exc))
    except hmrc_integration_operations.HMRCIntegrationException as exc:
        logging.warning(str(exc))
    except Exception as exc:  # noqa
        logging.warning(
            f"An unexpected error occurred when sending licence '{licence_id}' changes to HMRC Integration -> "
            f"{type(exc).__name__}: {exc}"
        )

    # Get the task
    task = Task.objects.filter(queue=TASK_QUEUE, task_params__contains=licence_id).first()

    # If the scan was triggered directly and not as a background task then no task will be found
    if not task:
        logging.warning(f"No task was found for licence '{licence_id}'")
    else:
        # Get the task's current attempt number by retrieving the previous attempts and adding 1
        current_attempt = task.attempts + 1

        # Schedule a new task if the current task has been attempted MAX_ATTEMPTS times
        if current_attempt >= MAX_ATTEMPTS:
            logging.warning(f"Maximum attempts of {MAX_ATTEMPTS} for licence '{licence_id}' has been reached")

            schedule = (current_attempt ** 4) + 5
            schedule_date = {timezone.now() + timedelta(seconds=schedule)}
            logging.info(f"Scheduling new task for licence '{licence_id}' for {schedule_date}")
            send_licence_changes_to_hmrc_integration(licence_id, schedule=schedule)

    # Raise an exception (this will cause the task to be marked as 'Failed')
    raise Exception(f"Failed to send licence '{licence_id}' changes to HMRC Integration")
