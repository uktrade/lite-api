from django.db import models

from conf.settings import S3_DOWNLOAD_LINK_EXPIREY_SECONDS
from documents.fields import S3FileField
from documents.utils import s3_client


class Document(models.Model):
    name = models.CharField(max_length=1000, null=False, blank=False)
    file = S3FileField(max_length=1000)
    size = models.IntegerField(null=True, blank=True)
    virus_scanned_at = models.DateTimeField(null=True, blank=True)
    safe = models.NullBooleanField()
    checksum = models.CharField(max_length=64, null=True, blank=True)

    @property
    def download_url(self):
        """
        Return a self expiring download link for a document stored on S3
        """
        s3 = s3_client()
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': self.s3_bucket,
                'Key': self.file.name
            },
            ExpiresIn=S3_DOWNLOAD_LINK_EXPIREY_SECONDS
        )
        return url

    @property
    def s3_bucket(self):
        return self.file.storage.bucket_name

    @property
    def s3_key(self):
        return self.file.name
