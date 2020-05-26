import uuid

from django.db import models

from common.models import TimestampableModel
from documents.libraries import s3_operations


class Document(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False, blank=False)
    s3_key = models.CharField(max_length=1000, null=False, blank=False, default=None)
    size = models.IntegerField(null=True, blank=True)
    virus_scanned_at = models.DateTimeField(null=True, blank=True)
    safe = models.NullBooleanField()

    def __str__(self):
        return self.name

    def delete_s3(self):
        """Removes document's file from S3."""

        s3_operations.delete_file(self.s3_key)

    def scan_for_viruses(self):
        """Asynchronously scans document's file on S3 for viruses."""

        from documents.av_scan import scan_document_for_viruses_task_for_viruses

        scan_document_for_viruses_task_for_viruses(self)
        self.refresh_from_db()

        if self.safe is False:
            self.delete_s3()

        return self.safe
