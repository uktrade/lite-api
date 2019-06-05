import uuid
from django.db import models

import reversion


@reversion.register()
class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60, default=None, blank=False, null=False)
