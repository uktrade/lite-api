from django.db import models


class BaseApplicationManager(models.Manager):
    def draft_applications(self, organisation):
        return self.get_queryset().filter(submitted_at__isnull=True, organisation=organisation)

    def submitted_applications(self, organisation):
        return self.get_queryset().filter(submitted_at__isnull=False, organisation=organisation)
