from celery import shared_task
from celery.utils.log import get_task_logger

from django.db import transaction
from api.documents.models import Document

MAX_ATTEMPTS = 7
RETRY_BACKOFF = 60


logger = get_task_logger(__name__)


@shared_task(
    bind=True,
)
def process_uploaded_document(self, document_id):
    """ """
    document = Document.objects.get(id=document_id)
    document.move_staged_document()
    scan_document_for_viruses.apply_async(args=(document_id,), link_error=delete_document_from_s3.si(document_id))


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
        except Exception:
            logger.exception("Document virus scan failed")
            raise


@shared_task
def delete_document_from_s3(document_id):
    logger.warning(
        "Maximum attempts of %s for document %s has been reached calling s3 delete", MAX_ATTEMPTS, document_id
    )
    document = Document.objects.get(id=document_id)
    # For now, always attempt to delete from both staged and processed S3 buckets..
    #   This is because we cannot be sure right now if we have moved over to using
    #   two buckets or not.  When we are using two S3 buckets, we can be more specific and ensure
    #   to only target the `delete_document_from_s3()` task at one of the S3 buckets
    document.delete_s3(bucket="staged")
    document.delete_s3(bucket="processed")
