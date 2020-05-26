import logging
import uuid

from django.db import models
from django.utils.timezone import now

from common.models import TimestampableModel
from documents.libraries import s3_operations, av_operations


class Document(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False, blank=False)
    s3_key = models.CharField(max_length=1000, null=False, blank=False, default=None)
    size = models.IntegerField(null=True, blank=True)
    virus_scanned_at = models.DateTimeField(null=True, blank=True)
    virus_scan_attempts = models.PositiveSmallIntegerField(default=0)
    safe = models.NullBooleanField()

    def __str__(self):
        return self.name

    def delete_s3(self):
        """Removes document's file from S3."""

        s3_operations.delete_file(self.id, self.s3_key)

    def scan_for_viruses(self):
        """Asynchronously retrieves document's file from S3 and scans it for viruses."""

        self.virus_scan_attempts += 1
        self.save()

        file = s3_operations.get_object(self.id, self.s3_key)
        is_file_clean = av_operations.scan_file_for_viruses(self.id, self.name, file)

        if is_file_clean is not None:
            self.safe = is_file_clean
            self.virus_scanned_at = now()
            self.save()

            if not is_file_clean:
                logging.warning(f"Document '{self.id}' is not safe")
                self.delete_s3()

        return self.safe
