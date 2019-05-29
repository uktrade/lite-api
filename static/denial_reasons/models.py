import reversion
from django.db import models


@reversion.register()
class DenialReason(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=3)
    deprecated = models.BooleanField(default=False, null=False, blank=False)
