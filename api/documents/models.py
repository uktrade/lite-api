import logging
import uuid

from django.db import models
from django.utils import timezone

from api.common.models import TimestampableModel
from api.documents.libraries import s3_operations, av_operations


logger = logging.getLogger(__name__)


class Document(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False, blank=False)
    # s3_key is not unique.  We can have many different Document records pointing to the same file in S3
    s3_key = models.CharField(max_length=1000, null=False, blank=False, default=None)
    size = models.IntegerField(null=True, blank=True)
    virus_scanned_at = models.DateTimeField(null=True, blank=True)
    safe = models.BooleanField(null=True)

    def __str__(self):
        return self.name

    def get_other_documents_sharing_file(self):
        return Document.objects.filter(s3_key=self.s3_key).exclude(pk=self.pk)

    def delete_s3(self, *, force_delete=False):
        """Removes the document's file from S3."""
        file_shared_with_other_documents = self.get_other_documents_sharing_file().exists()
        if not force_delete and file_shared_with_other_documents:
            logger.info("Shared file %s was not deleted", self.s3_key)
            return

        s3_operations.delete_file(self.id, self.s3_key)

    def set_virus_scan_result(self, document, is_safe, virus_scanned_at):
        document.safe = is_safe
        document.virus_scanned_at = virus_scanned_at
        document.save()

    def scan_for_viruses(self):
        """Retrieves the document's file from S3 and scans it for viruses."""

        file = s3_operations.get_object(self.id, self.s3_key)

        if not file:
            logger.warning(
                "Failed to retrieve file `%s` from S3 for document `%s` for virus scan",
                self.s3_key,
                self.id,
            )

        is_safe = not av_operations.scan_file_for_viruses(self.id, self.name, file)
        virus_scanned_at = timezone.now()
        self.set_virus_scan_result(self, is_safe, virus_scanned_at)

        if not is_safe:
            logger.warning("Document `%s` is not safe", self.id)
            self.delete_s3(force_delete=True)
            file_shared_with_other_documents = self.get_other_documents_sharing_file()
            for other_document in file_shared_with_other_documents:
                logger.warning("Other document `%s` is not safe because `%s` is not safe", other_document.id, self.id)
                self.set_virus_scan_result(other_document, is_safe, virus_scanned_at)

        return is_safe
