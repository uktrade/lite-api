import uuid

import reversion
from django.db import models


@reversion.register()
class CaseType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False, null=False)
