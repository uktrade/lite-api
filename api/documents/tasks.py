import logging

from background_task import background
from background_task.models import Task
from django.db import transaction

from api.conf.settings import MAX_ATTEMPTS
from api.documents.libraries.av_operations import VirusScanException
from api.documents.models import Document

TASK_QUEUE = "document_av_scan_queue"


@background(queue=TASK_QUEUE, schedule=0)
def scan_document_for_viruses(document_id, scheduled_as_background_task=True):
    """
    Scans documents for viruses
    :param document_id:
    :param scheduled_as_background_task: Has this function has been scheduled as a task (used for error handling)
    """

    with transaction.atomic():
        logging.info(f"Fetching document '{document_id}'")
        document = Document.objects.select_for_update(nowait=True).get(id=document_id)

        if document.virus_scanned_at:
            logging.info(f"Document '{document_id}' has already been scanned; safe={document.safe}")
            return

        try:
            document.scan_for_viruses()
        except VirusScanException as exc:
            _handle_exception(str(exc), document, scheduled_as_background_task)
        except Exception as exc:  # noqa
            _handle_exception(
                f"An unexpected error occurred when scanning document '{document_id}' -> {type(exc).__name__}: {exc}",
                document,
                scheduled_as_background_task,
            )


def _handle_exception(message: str, document, scheduled_as_background_task):
    logging.warning(message)
    error_message = f"Failed to scan document '{document.id}'"

    if scheduled_as_background_task:
        try:
            task = Task.objects.filter(queue=TASK_QUEUE, task_params__contains=document.id)
        except Task.DoesNotExist:
            logging.error(f"No task was found for document '{document.id}'")
            document.delete_s3()
        else:
            # Get the task's current attempt number by retrieving the previous attempts and adding 1
            current_attempt = task.first().attempts + 1

            # Delete the document's file from S3 if the task has been attempted MAX_ATTEMPTS times
            if current_attempt >= MAX_ATTEMPTS:
                logging.warning(f"Maximum attempts of {MAX_ATTEMPTS} for document '{document.id}' has been reached")
                document.delete_s3()

            error_message += f"; attempt number {current_attempt}"
    else:
        document.delete_s3()

    # Raise an exception.
    # This will result in a serializer error or
    # cause the task to be marked as 'Failed' and retried if there are retry attempts left
    raise Exception(error_message)
