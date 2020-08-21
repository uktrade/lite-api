import uuid

from django.db import models


class LetterLayout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()  # Friendly name
    filename = models.TextField()  # Letter file name minus extension

    class Meta:
        ordering = ["name"]
