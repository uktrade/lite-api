from botocore.exceptions import ClientError
from celery import shared_task
from celery.utils.log import get_task_logger

from api.documents.libraries.s3_operations import get_object
from api.documents.models import Document
from api.document_data.models import DocumentData


logger = get_task_logger(__name__)


MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180


@shared_task(
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def backup_document_data():
    """Backup document data into the database."""
    for document in Document.objects.filter(safe=True):
        try:
            file = get_object(document.id, document.s3_key)
        except ClientError:
            logger.warning(f"Failed to retrieve file '{document.s3_key}' from S3 for document '{document.id}'")
            continue

        if not file:
            logger.warning(f"Failed to retrieve file '{document.s3_key}' from S3 for document '{document.id}'")
            continue

        try:
            document_data = DocumentData.objects.get(s3_key=document.s3_key)
        except DocumentData.DoesNotExist:
            DocumentData.objects.create(
                data=file["Body"].read(),
                last_modified=file["LastModified"],
                s3_key=document.s3_key,
            )
            logger.info(f"Created '{document.s3_key}' for document '{document.id}'")
            continue

        if file["LastModified"] > document_data.last_modified:
            document_data.last_modified = file["LastModified"]
            document_data.data = file["Body"].read()
            document_data.save()
            logger.info(f"Updated '{document.s3_key}' for document '{document.id}'")
