from django.db import models


class BaseApplicationManager(models.Manager):
    def drafts(self, organisation):
        return self.get_queryset().filter(status__isnull=True, organisation=organisation)

    def submitted(self, organisation):
        return self.get_queryset().filter(status__isnull=False, organisation=organisation)
