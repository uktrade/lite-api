import uuid

import reversion
from django.db import models


@reversion.register()
class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60, default=None, blank=False, null=False)
