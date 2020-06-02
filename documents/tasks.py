import logging

from background_task import background
from background_task.models import Task
from django.db import transaction

from conf.settings import MAX_ATTEMPTS
from documents.libraries.av_operations import VirusScanException
from documents.models import Document

TASK_QUEUE = "document_av_scan_queue"


@background(schedule=0, queue=TASK_QUEUE)
def scan_document_for_viruses(document_id, is_background_task=True):
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

    if is_background_task:
        try:
            task = Task.objects.get(queue=TASK_QUEUE, task_params__contains=document_id)
        except Task.DoesNotExist:
            logging.error(f"No task was found for document '{document_id}'")
            doc.delete_s3()
        else:
            # Get the task's current attempt number by retrieving the previous attempts and adding 1
            current_attempt = task.attempts + 1

            # Delete the document's file from S3 if the task has been attempted MAX_ATTEMPTS times
            if current_attempt >= MAX_ATTEMPTS:
                logging.warning(f"Maximum attempts of {MAX_ATTEMPTS} for document '{document_id}' has been reached")
                doc.delete_s3()
    else:
        doc.delete_s3()

    # Raise an exception (this will result in a serializer error or cause the task (if any) to be marked as 'Failed')
    raise Exception(f"Failed to scan document '{document_id}'")
