import uuid

from django.db import models

from conf.settings import env
from documents.utils import s3_client


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False, blank=False)
    s3_key = models.CharField(max_length=1000, null=False, blank=False, default=None)
    size = models.IntegerField(null=True, blank=True)
    virus_scanned_at = models.DateTimeField(null=True, blank=True)
    safe = models.NullBooleanField()
    checksum = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.name

    def delete(self, **kwargs):
        s3_client().delete_object(Bucket=env('AWS_STORAGE_BUCKET_NAME'), Key=self.s3_key)
        super().delete()

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
            - get the checksum/etag
        """
        try:
            # self.update_md5_checksum()
            self.scan_for_viruses()
            if self.safe is False:
                self.delete()
            return bool(self.checksum) and self.safe
        except Exception:
            return False

    # def update_md5_checksum(self):
    #     """
    #     Update the md5 checksum on the document record
    #     """
    #     self.checksum = self.get_md5_checksum()
    #     self.save()

