from botocore.exceptions import ClientError
from celery import shared_task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.utils import timezone

from api.documents.libraries.s3_operations import get_object
from api.documents.models import Document
from api.document_data.models import (
    BackupLog,
    DocumentData,
)


logger = get_task_logger(__name__)


MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180


@shared_task(
    autoretry_for=(Exception,),
    bind=True,
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def backup_document_data(self):
    """Backup document data into the database."""

    # When running this command by hand it's best to set the logging as follows:
    #    import logging
    #    from api.document_data.celery_tasks import logger
    #    logger.setLevel(logging.DEBUG)
    #    from api.documents.libraries.s3_operations import logger
    #    logger.setLevel(logging.WARNING)
    #
    # This will ensure that you get the debug output of this particular file but
    # miss the extra info from the get_object call

    if not settings.BACKUP_DOCUMENT_DATA_TO_DB:
        logger.info("Skipping backup document data to db")
        return

    backup_log = BackupLog.objects.create(task_id=self.request.id)

    safe_documents = Document.objects.filter(safe=True)
    count = safe_documents.count()
    logger.debug(
        "Backing up %s documents",
        count,
    )
    for index, (document_id, document_s3_key) in enumerate(safe_documents.values_list("pk", "s3_key"), start=1):
        logger.debug(
            "Processing %s of %s",
            index,
            count,
        )
        try:
            file = get_object(document_id, document_s3_key)
        except ClientError:
            logger.warning(
                "Failed to retrieve file '%s' from S3 for document '%s'",
                document_s3_key,
                document_id,
            )
            continue

        if not file:
            logger.warning(
                "Failed to retrieve file '%s' from S3 for document '%s'",
                document_s3_key,
                document_id,
            )
            continue

        try:
            document_data = DocumentData.objects.get(s3_key=document_s3_key)
        except DocumentData.DoesNotExist:
            DocumentData.objects.create(
                data=file["Body"].read(),
                last_modified=file["LastModified"],
                s3_key=document_s3_key,
                content_type=file["ContentType"],
            )
            logger.info(
                "Created '%s' for document '%s'",
                document_s3_key,
                document_id,
            )
            file["Body"].close()
            del file  # Clear this out for garbage collection
            continue

        if file["LastModified"] > document_data.last_modified:  # noqa: WS03
            document_data.last_modified = file["LastModified"]  # noqa: WS03
            document_data.data = file["Body"].read()  # noqa: WS03
            document_data.content_type = file["ContentType"]  # noqa: WS03
            document_data.save()
            logger.info(
                "Updated '%s' for document '%s'",
                document_s3_key,
                document_id,
            )
            file["Body"].close()  # noqa: WS03
            del file  # Clear this out for garbage collection
            continue

        logger.debug(
            "Nothing required for '%s' for document '%s'",
            document_s3_key,
            document_id,
        )

    backup_log.ended_at = timezone.now()
    backup_log.save()

    logger.debug("Completed backing up documents")
