import logging
import uuid

from django.db import models
from django.utils.timezone import now

from api.common.models import TimestampableModel
from api.documents.libraries import s3_operations, av_operations


class Document(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False, blank=False)
    s3_key = models.CharField(max_length=1000, null=False, blank=False, default=None)
    size = models.IntegerField(null=True, blank=True)
    virus_scanned_at = models.DateTimeField(null=True, blank=True)
    safe = models.NullBooleanField()

    is_content_english = models.BooleanField(null=True, help_text="Is the document in English?")
    includes_company_letterhead = models.BooleanField(
        null=True, help_text="Does the document include at least one page on company letterhead?"
    )

    def __str__(self):
        return self.name

    def delete_s3(self):
        """Removes the document's file from S3."""

        s3_operations.delete_file(self.id, self.s3_key)

    def scan_for_viruses(self):
        """Retrieves the document's file from S3 and scans it for viruses."""

        file = s3_operations.get_object(self.id, self.s3_key)

        if not file:
            logging.warning(f"Failed to retrieve file '{self.s3_key}' from S3 for document '{self.id}'")

        self.safe = not av_operations.scan_file_for_viruses(self.id, self.name, file)
        self.virus_scanned_at = now()
        self.save()

        if not self.safe:
            logging.warning(f"Document '{self.id}' is not safe")
            self.delete_s3()

        return self.safe
