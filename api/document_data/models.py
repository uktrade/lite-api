import uuid

from django.db import models

from celery.result import AsyncResult

from api.common.models import TimestampableModel


class DocumentData(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    s3_key = models.CharField(unique=True, max_length=1000)
    data = models.BinaryField()
    last_modified = models.DateTimeField()
    content_type = models.CharField(max_length=255)


class BackupLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)
    task_id = models.UUIDField()

    class Meta:
        get_latest_by = ["started_at"]
        ordering = ["started_at"]

    def get_async_result(self):
        return AsyncResult(str(self.task_id))
