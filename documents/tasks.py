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
            logging.info(f"Document '{document_id}' has already been scanned; is_safe={doc.is_safe}")
            return doc.is_safe

        try:
            return doc.scan_for_viruses()
        except VirusScanException as exc:
            logging.warning(str(exc))
        except Exception as exc:  # noqa
            logging.warning(f"An unexpected error occurred when scanning document '{document_id}': {exc}")

        current_task = Task.objects.get(queue=TASK_QUEUE, task_params__contains=document_id)
        current_attempt = current_task.attempts + 1

        if current_attempt >= settings.MAX_ATTEMPTS:
            logging.warning(f"MAX_ATTEMPTS {settings.MAX_ATTEMPTS} for document '{document_id}' has been reached")
            doc.delete_s3()

    raise Exception(f"Failed to scan document '{document_id}'")
