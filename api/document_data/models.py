import uuid

from django.db import models

from api.common.models import TimestampableModel


class DocumentData(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    s3_key = models.CharField(unique=True, max_length=1000)
    data = models.BinaryField()
    last_modified = models.DateTimeField()
    content_type = models.CharField(max_length=255)
