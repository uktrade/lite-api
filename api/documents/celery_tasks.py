from celery import shared_task
from celery.utils.log import get_task_logger

from django.db import transaction
from api.documents.models import Document

MAX_ATTEMPTS = 7
RETRY_BACKOFF = 60


logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def scan_document_for_viruses(self, document_id):
    """
    Scans documents for viruses
    :param document_id:
    """
    with transaction.atomic():
        logger.info("Fetching document %s", document_id)

        document = Document.objects.select_for_update(nowait=True).get(id=document_id)
        if document.virus_scanned_at:
            logger.info("Document %s has already been scanned; safe=%s", document_id, document.safe)
            return

        try:
            document.scan_for_viruses()
        except Exception as exc:  # noqa
            logger.exception("Document virus scan failed")
            raise


@shared_task
def delete_document_from_s3(document_id):
    logger.warning(
        "Maximum attempts of %s for document %s has been reached calling s3 delete", MAX_ATTEMPTS, document_id
    )
    document = Document.objects.get(id=document_id)
    document.delete_s3()
