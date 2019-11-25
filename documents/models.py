import logging
import uuid

from django.db import models

from conf import settings
from documents.helpers import DocumentOperation
from documents.utils import s3_client


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False, blank=False)
    s3_key = models.CharField(max_length=1000, null=False, blank=False, default=None)
    size = models.IntegerField(null=True, blank=True)
    virus_scanned_at = models.DateTimeField(null=True, blank=True)
    safe = models.NullBooleanField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.name

    def delete_s3(self, **kwargs):
        """ Removes file from s3 bucket (eg when the file is virus infected) """
        logging.info("Removing file from S3: " + self.s3_key)
        DocumentOperation().delete_file(self.s3_key)

    def scan_for_viruses(self):
        from documents.av_scan import virus_scan_document

        virus_scan_document(self.id)
        self.refresh_from_db()
        return self

    def prepare_document(self):
        """
        Prepares the document for usage. This is run async after the document
        is already on S3.
            - perform a virus check
        """
        self.scan_for_viruses()
        if self.safe is False:
            self.delete_s3()
        return self.safe
