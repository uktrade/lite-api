import uuid

from django.db import models

from applications.models import Application


class Queue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default='Untitled Queue')
    applications = models.ManyToManyField(Application)
