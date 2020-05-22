import logging

from background_task import background

from documents.av_scan import VirusScanException


@background(schedule=0, queue="document_av_scan_queue")
def prepare_document(document_id):
    """
    Post upload process (virus scan etc).
    Executed by background worker process or synchronous depending on BACKGROUND_TASK_RUN_ASYNC.
    """
    from documents.models import Document

    logging.info(f"Preparing document {document_id}")

    try:
        doc = Document.objects.get(id=document_id)
        doc.scan_for_viruses()
    except VirusScanException as exc:
        raise exc
    except Exception as exc:
        raise Exception(f"An unexpected error occurred when preparing document {document_id}: {exc}")
