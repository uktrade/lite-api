from django.db import models


class DenialReason(models.Model):
    id = models.TextField(primary_key=True, editable=False)
    deprecated = models.BooleanField(default=False, null=False, blank=False)
    description = models.TextField(default="")

    class Meta:
        ordering = ["id"]
