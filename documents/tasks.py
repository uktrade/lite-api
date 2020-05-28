import logging

from background_task import background
from background_task.models import Task
from django.db import transaction

from conf.settings import MAX_ATTEMPTS as TASK_UNIVERSAL_MAX_ATTEMPTS
from documents.libraries.av_operations import VirusScanException
from documents.models import Document

TASK_QUEUE = "document_av_scan_queue"
TASK_SPECIFIC_MAX_ATTEMPTS = 7  # Must be lower than settings.MAX_ATTEMPTS or document will not be deleted from S3


@background(schedule=0, queue=TASK_QUEUE)
def scan_document_for_viruses(document_id):
    """
    Executed by background worker process or synchronous depending on BACKGROUND_TASK_RUN_ASYNC.
    """

    with transaction.atomic():
        logging.info(f"Fetching document '{document_id}'")
        doc = Document.objects.select_for_update(nowait=True).get(id=document_id)

        if doc.virus_scanned_at:
            logging.info(f"Document '{document_id}' has already been scanned; safe={doc.safe}")
            return

        try:
            doc.scan_for_viruses()
            return
        except VirusScanException as exc:
            logging.warning(str(exc))
        except Exception as exc:  # noqa
            logging.warning(
                f"An unexpected error occurred when scanning document '{document_id}' -> {type(exc).__name__}: {exc}"
            )

        # Get the task
        task = Task.objects.filter(queue=TASK_QUEUE, task_params__contains=document_id).first()

        # If the scan was triggered directly and not as a background task then no task will be found
        if not task:
            logging.warning(f"No task was found for document '{document_id}'")
            doc.delete_s3()
        else:
            # Get the task's current attempt number by retrieving the previous attempt number and adding 1
            current_attempt = task.attempt + 1

            # Delete the document's file from S3 if the task has been attempted TASK_SPECIFIC_MAX_ATTEMPTS times
            if current_attempt >= TASK_SPECIFIC_MAX_ATTEMPTS:
                logging.warning(
                    f"Maximum attempts of {TASK_SPECIFIC_MAX_ATTEMPTS} for document '{document_id}' has been reached"
                )
                doc.delete_s3()

                # Set the task's attempt to settings.MAX_ATTEMPTS so that it will be deleted by the orchestration layer
                task.attempt = TASK_UNIVERSAL_MAX_ATTEMPTS - 1
                task.save()

        # Raise an exception (this will cause the task to be marked as 'Failed')
        raise Exception(f"Failed to scan document '{document_id}'")
