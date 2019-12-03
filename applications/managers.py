from django.db import models

from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class BaseApplicationManager(models.Manager):
    def drafts(self, organisation):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().filter(status=draft, organisation=organisation).order_by("-created")

    def submitted(self, organisation):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().filter(organisation=organisation).exclude(status=draft).order_by("-submitted_at")


class HmrcQueryManager(models.Manager):
    def drafts(self, hmrc_organisation):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().filter(status=draft, hmrc_organisation=hmrc_organisation).order_by("-created")

    def submitted(self, hmrc_organisation):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return (
            self.get_queryset()
            .filter(hmrc_organisation=hmrc_organisation)
            .exclude(status=draft)
            .order_by("-submitted_at")
        )
