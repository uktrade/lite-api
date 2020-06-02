import logging
from datetime import timedelta

from background_task import background
from background_task.models import Task
from django.utils import timezone

from conf.settings import MAX_ATTEMPTS
from licences.libraries import hmrc_integration_operations
from licences.models import Licence

TASK_QUEUE = "hmrc_integration_queue"
TASK_BACK_OFF = 3600  # Time, in seconds, to wait before scheduling a new task (used after MAX_ATTEMPTS is reached)


@background(schedule=0, queue=TASK_QUEUE)
def send_licence_to_hmrc_integration(licence_id, is_background_task=True):
    logging.info(f"Sending licence '{licence_id}' changes to HMRC Integration")

    licence = Licence.objects.get(id=licence_id)

    try:
        hmrc_integration_operations.send_licence(licence)
        return
    except hmrc_integration_operations.HMRCIntegrationException as exc:
        logging.warning(str(exc))
    except Exception as exc:  # noqa
        logging.warning(
            f"An unexpected error occurred when sending licence '{licence_id}' changes to HMRC Integration -> "
            f"{type(exc).__name__}: {exc}"
        )

    error_message = f"Failed to send licence '{licence_id}' changes to HMRC Integration"

    if is_background_task:
        try:
            task = Task.objects.get(queue=TASK_QUEUE, task_params__contains=licence_id)
        except Task.DoesNotExist:
            logging.error(f"No task was found for licence '{licence_id}'")
        else:
            # Get the task's current attempt number by retrieving the previous attempts and adding 1
            current_attempt = task.attempts + 1

            # Schedule a new task if the current task has been attempted MAX_ATTEMPTS times;
            # HMRC Integration tasks need to be resilient and keep retrying post-failure indefinitely.
            # This logic will make MAX_ATTEMPTS attempts to send licence changes according to the Django Background Task
            # Runner scheduling, then wait TASK_BACK_OFF seconds before starting the process again.
            if current_attempt >= MAX_ATTEMPTS:
                schedule_max_tried_task_as_new_task(licence_id)

        # Raise an exception (this will cause the task to be marked as 'Failed')
        raise Exception(error_message)
    else:
        logging.error(error_message)


def schedule_max_tried_task_as_new_task(licence_id):
    logging.warning(f"Maximum attempts of {MAX_ATTEMPTS} for licence '{licence_id}' has been reached")

    schedule_datetime = {timezone.now() + timedelta(seconds=TASK_BACK_OFF)}
    logging.info(f"Scheduling new task for licence '{licence_id}' to commence at {schedule_datetime}")
    send_licence_to_hmrc_integration(licence_id, schedule=TASK_BACK_OFF)  # noqa
