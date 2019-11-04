from django.db import models
from django.utils import timezone


class Timestamp(models.Model):
    created_at = models.DateTimeField(editable=False, db_index=True, null=True)
    updated_at = models.DateTimeField(db_index=True, null=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

