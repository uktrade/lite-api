from django.db import models


class BaseApplicationManager(models.Manager):
    def get_drafts(self, organisation):
        return self.get_queryset().filter(submitted_at__isnull=True, organisation=organisation)

    def get_submitted(self, organisation):
        return self.get_queryset().filter(submitted_at__isnull=False, organisation=organisation)
