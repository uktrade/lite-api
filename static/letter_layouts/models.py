import uuid

from django.db import models


class LetterLayout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(help_text="Friendly name")
    filename = models.TextField(help_text="Letter file name minus extension")

    class Meta:
        ordering = ['name']
