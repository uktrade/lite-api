import uuid

from django.db import models

from api.users.models import GovUser


class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(blank=True)
    filter_json = models.JSONField()
    user = models.ForeignKey(GovUser, on_delete=models.CASCADE)
