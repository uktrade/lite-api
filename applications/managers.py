from django.db import models


class BaseApplicationManager(models.Manager):
    def drafts(self, organisation):
        return self.get_queryset().filter(status="Draft", organisation=organisation)

    def submitted(self, organisation):
        return self.get_queryset().exlude(status="Draft").filter(organisation=organisation)


class HmrcQueryManager(models.Manager):
    def drafts(self, hmrc_organisation):
        return self.get_queryset().filter(status="Draft", hmrc_organisation=hmrc_organisation)

    def submitted(self, hmrc_organisation):
        return self.get_queryset().exlude(status="Draft").filter(hmrc_organisation=hmrc_organisation)
