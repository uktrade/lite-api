import uuid

from django.db import models

from api.common.models import TimestampableModel


class Appeal(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grounds_for_appeal = models.TextField()
