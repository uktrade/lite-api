import logging

from background_task import background
from django.db import transaction

from conf import settings
from documents.libraries.av_operations import VirusScanException


@background(schedule=0, queue="document_av_scan_queue")
def scan_document_for_viruses_task(document_id):
    """
    Executed by background worker process or synchronous depending on BACKGROUND_TASK_RUN_ASYNC.
    """
    from documents.models import Document

    logging.info(f"Fetching document {document_id}")

    with transaction.atomic():
        doc = Document.objects.select_for_update(nowait=True).get(id=document_id)

        if doc.virus_scanned_at:
            logging.info(f"Skipping scan of document {doc.id}; already performed on {doc.virus_scanned_at}")
            return

        try:
            doc.scan_for_viruses()
        except VirusScanException as exc:
            error = str(exc)
        except Exception as exc:  # noqa
            error = f"An unexpected error occurred when scanning document {document_id}: {exc}"

        if error:
            logging.warning(error)

            if doc.virus_scan_attempts == settings.MAX_ATTEMPTS:
                logging.warning(f"{settings.MAX_ATTEMPTS} for document {doc.id} has been reached")
                doc.delete_s3()

            raise Exception(f"Failed to scan document {doc.id}")
