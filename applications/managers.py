from django.db import models


class BaseApplicationManager(models.Manager):
    def drafts(self, organisation):
        return self.get_queryset().filter(status__isnull=True, organisation=organisation).order_by("-created")

    def submitted(self, organisation):
        return self.get_queryset().filter(status__isnull=False, organisation=organisation).order_by("-submitted_at")


class HmrcQueryManager(models.Manager):
    def drafts(self, hmrc_organisation):
        return self.get_queryset().filter(status__isnull=True, hmrc_organisation=hmrc_organisation).order_by("-created")

    def submitted(self, hmrc_organisation):
        return (
            self.get_queryset()
            .filter(status__isnull=False, hmrc_organisation=hmrc_organisation)
            .order_by("-submitted_at")
        )
