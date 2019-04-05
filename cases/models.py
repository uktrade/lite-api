import uuid

from django.db import models

from applications.models import Application


class Case(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, related_name='case', on_delete=models.CASCADE)
