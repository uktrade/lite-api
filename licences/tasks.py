import logging
from datetime import timedelta

from background_task import background
from background_task.models import Task
from django.db import transaction
from django.utils import timezone

from conf.settings import MAX_ATTEMPTS, BACKGROUND_TASK_ENABLED
from licences.libraries import hmrc_integration_operations
from licences.models import Licence

TASK_QUEUE = "hmrc_integration_queue"
TASK_BACK_OFF = 3600  # Time, in seconds, to wait before scheduling a new task (used after MAX_ATTEMPTS is reached)


def schedule_licence_for_hmrc_integration(licence_id, action):
    if BACKGROUND_TASK_ENABLED:
        logging.info(f"Scheduling licence '{licence_id}', action '{action}' for HMRC Integration")
        task = Task.objects.filter(queue=TASK_QUEUE, task_params=f'[["{licence_id}", "{action}"], {{}}]')

        if task.exists():
            logging.info(f"Licence '{licence_id}', action '{action}' has already been scheduled")
        else:
            send_licence_to_hmrc_integration(licence_id, action)
            logging.info(f"Licence '{licence_id}', action '{action}' has been scheduled")
    else:
        send_licence_to_hmrc_integration.now(licence_id, action, scheduled_as_background_task=False)


def schedule_max_tried_task_as_new_task(licence_id, action):
    """
    Used to schedule a max-tried task as a new task (starting from attempts=0)
    This function was abstracted from 'send_licence_to_hmrc_integration' to enable unit testing of a recursive operation
    """
    logging.warning(
        f"Maximum attempts of {MAX_ATTEMPTS} for licence '{licence_id}', action '{action}' has been reached"
    )

    schedule_datetime = timezone.now() + timedelta(seconds=TASK_BACK_OFF)
    logging.info(
        f"Scheduling new task for licence '{licence_id}', action '{action}' to commence at {schedule_datetime}"
    )
    send_licence_to_hmrc_integration(licence_id, action, schedule=TASK_BACK_OFF)  # noqa


@background(queue=TASK_QUEUE, schedule=0)
def send_licence_to_hmrc_integration(licence_id, action, scheduled_as_background_task=True):
    """
    Sends licence details to HMRC Integration
    :param licence_id:
    :param licence_reference:
    :param scheduled_as_background_task: Has this function has been scheduled as a task (used for error handling)
    """

    try:
        with transaction.atomic():
            # transaction.atomic + select_for_update + nowait=True will throw an error if row has already been locked
            licence = Licence.objects.select_for_update(nowait=True).get(id=licence_id)
            hmrc_integration_operations.send_licence(licence, action)
    except hmrc_integration_operations.HMRCIntegrationException as exc:
        _handle_exception(str(exc), licence_id, action, scheduled_as_background_task)
    except Exception as exc:  # noqa
        _handle_exception(
            f"An unexpected error occurred when sending licence '{licence_id}', action '{action}' to HMRC Integration "
            f"-> {type(exc).__name__}: {exc}",
            licence_id,
            action,
            scheduled_as_background_task,
        )


def _handle_exception(message, licence_id, action, scheduled_as_background_task):
    logging.warning(message)
    error_message = f"Failed to send licence '{licence_id}', action '{action}' to HMRC Integration"

    if scheduled_as_background_task:
        try:
            task = Task.objects.get(queue=TASK_QUEUE, task_params=f'[["{licence_id}", "{action}"], {{}}]')
        except Task.DoesNotExist:
            logging.error(f"No task was found for licence '{licence_id}', action '{action}'")
        else:
            # Get the task's current attempt number by retrieving the previous attempts and adding 1
            current_attempt = task.attempts + 1

            # Schedule a new task if the current task has been attempted MAX_ATTEMPTS times;
            # HMRC Integration tasks need to be resilient and keep retrying post-failure indefinitely.
            # This logic will make MAX_ATTEMPTS attempts to send licence changes according to the Django Background Task
            # Runner scheduling, then wait TASK_BACK_OFF seconds before starting the process again.
            if current_attempt >= MAX_ATTEMPTS:
                schedule_max_tried_task_as_new_task(licence_id, action)

        # Raise an exception
        # this will cause the task to be marked as 'Failed' and retried if there are retry attempts left
        raise Exception(error_message)
    else:
        logging.error(error_message)
