import uuid

from django.db import models

from api.common.models import TimestampableModel
from api.documents.models import Document


class Appeal(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grounds_for_appeal = models.TextField()


class AppealDocument(Document):
    appeal = models.ForeignKey(
        Appeal,
        on_delete=models.CASCADE,
        related_name="documents",
    )
