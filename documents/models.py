import uuid

from django.conf import settings
from django.db import models
from django.db.models import CASCADE

from cases.models import Case
from documents.fields import S3FileField
from goods.models import Good
from organisations.models import Organisation


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
            ExpiresIn=settings.S3_DOWNLOAD_LINK_EXPIREY_SECONDS
        )
        return url

    @property
    def s3_bucket(self):
        return self.file.storage.bucket_name

    @property
    def s3_key(self):
        return self.file.name


class InternalDocument(Document):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=CASCADE)


# class ExporterDocument(Document):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     organisation = models.ForeignKey(Organisation, on_delete=CASCADE)
#
#
# class ExporterGoodDocument(ExporterDocument):
#     good = models.ForeignKey(Good, on_delete=CASCADE)
