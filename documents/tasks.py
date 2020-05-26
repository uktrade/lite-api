import logging

from background_task import background

from documents.av_scan import VirusScanException


@background(schedule=0, queue="document_av_scan_queue")
def scan_document_for_viruses_task(document_id):
    """
    Executed by background worker process or synchronous depending on BACKGROUND_TASK_RUN_ASYNC.
    """
    from documents.models import Document

    logging.info(f"Fetching document {document_id}")

    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        raise VirusScanException(f"Document {document_id} was not found")

    try:
        doc.scan_for_viruses()
    except VirusScanException as exc:
        raise exc
    except Exception as exc:
        raise VirusScanException(f"An unexpected error occurred when scanning document {document_id}: {exc}")
