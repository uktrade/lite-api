import uuid

from django.db import models

from cases.models import Case


class Queue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default='Untitled Queue')
    cases = models.ManyToManyField(Case)
