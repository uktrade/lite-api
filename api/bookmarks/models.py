import uuid

from django.db import models

from api.users.models import GovUser


class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.CharField(max_length=2000)
    user = models.ForeignKey(GovUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=200, blank=True)
