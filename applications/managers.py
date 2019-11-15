from django.db import models


class BaseApplicationManager(models.Manager):
    def drafts(self, organisation):
        return self.get_queryset().filter(
            status__isnull=True, organisation=organisation
        )

    def submitted(self, organisation):
        return self.get_queryset().filter(
            status__isnull=False, organisation=organisation
        )


class HmrcQueryManager(models.Manager):
    def drafts(self, hmrc_organisation):
        return self.get_queryset().filter(
            status__isnull=True, hmrc_organisation=hmrc_organisation
        )

    def submitted(self, hmrc_organisation):
        return self.get_queryset().filter(
            status__isnull=False, hmrc_organisation=hmrc_organisation
        )
