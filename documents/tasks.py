import logging

from background_task import background
from background_task.models import Task
from django.db import transaction

from conf import settings
from documents.libraries.av_operations import VirusScanException

TASK_QUEUE = "document_av_scan_queue"


@background(schedule=0, queue=TASK_QUEUE)
def scan_document_for_viruses(document_id):
    """
    Executed by background worker process or synchronous depending on BACKGROUND_TASK_RUN_ASYNC.
    """

    from documents.models import Document

    with transaction.atomic():
        logging.info(f"Fetching document '{document_id}'")
        doc = Document.objects.select_for_update(nowait=True).get(id=document_id)

        if doc.virus_scanned_at:
            logging.info(f"Document '{document_id}' has already been scanned; safe={doc.safe}")
            return doc.safe

        try:
            return doc.scan_for_viruses()
        except VirusScanException as exc:
            logging.warning(str(exc))
        except Exception as exc:  # noqa
            logging.warning(
                f"An unexpected error occurred when scanning document '{document_id}' -> {type(exc).__name__}: {exc}"
            )

        # Get the task's current attempt number by retrieving the previous attempt number and adding 1
        previous_attempt = (
            Task.objects.filter(queue=TASK_QUEUE, task_params__contains=document_id)
            .values_list("attempts", flat=True)
            .first()
        )
        current_attempt = previous_attempt + 1

        if current_attempt >= settings.MAX_ATTEMPTS:
            logging.warning(f"MAX_ATTEMPTS {settings.MAX_ATTEMPTS} for document '{document_id}' has been reached")
            doc.delete_s3()

    # Raise an exception (this will cause the task to be marked as 'Failed' and the attempt number to be updated)
    raise Exception(f"Failed to scan document '{document_id}'")
