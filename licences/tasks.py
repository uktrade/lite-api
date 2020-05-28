import logging

from background_task import background

from cases.libraries import hmrc_integration_operations
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

    # Raise an exception (this will cause the task to be marked as 'Failed')
    raise Exception(f"Failed to send licence '{licence_id}' changes to HMRC Integration")
