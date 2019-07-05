import uuid

import reversion
from django.db import models

from applications.models import Application
from conf.settings import S3_DOWNLOAD_LINK_EXPIREY_SECONDS, AWS_STORAGE_BUCKET_NAME
from documents.utils import s3_client
from gov_users.models import GovUser
from queues.models import Queue


@reversion.register()
class Case(models.Model):
    """
    Wrapper for application model intended for internal users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, related_name='case', on_delete=models.CASCADE)
    queues = models.ManyToManyField(Queue, related_name='cases')


@reversion.register()
class CaseNote(models.Model):
    """
    Note on a case, visible by internal users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name='case_note', on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, related_name='case_note', on_delete=models.CASCADE, default=None, null=False)
    text = models.TextField(default=None, blank=True, null=True, max_length=2200)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)


class CaseAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    users = models.ManyToManyField(GovUser, related_name='case_assignments')
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)


class CaseDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False, blank=False, default=None)
    size = models.IntegerField(null=True, blank=True)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    @property
    def download_url(self):
        """
        Return a self expiring download link for a document stored on S3
        """
        s3 = s3_client()
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': AWS_STORAGE_BUCKET_NAME,
                'Key': self.s3_key
            },
            ExpiresIn=S3_DOWNLOAD_LINK_EXPIREY_SECONDS
        )
        return url

    @property
    def s3_key(self):
        return self.name
