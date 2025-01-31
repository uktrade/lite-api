from django.db import models

from api.cases.enums import (
    CaseTypeSubTypeEnum,
    CaseTypeTypeEnum,
)
from api.cases.models import (
    Case,
    CaseType,
)
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class F680ApplicationQuerySet(models.QuerySet):
    def get_prepared_object(self, pk):
        return self.get(pk=pk)


class F680Application(Case):  # /PS-IGNORE
    application = models.JSONField()

    objects = F680ApplicationQuerySet.as_manager()

    def save(self, *args, **kwargs):
        try:
            _ = self.case_type
        except self.__class__.case_type.RelatedObjectDoesNotExist:
            self.case_type = CaseType.objects.get(
                sub_type=CaseTypeSubTypeEnum.F680,
                type=CaseTypeTypeEnum.APPLICATION,
            )

        if not self.status:
            self.status = get_case_status_by_status(CaseStatusEnum.DRAFT)

        return super().save(*args, **kwargs)

    def validate_application_ready_for_submission(self):
        return {}

    def on_submit(self, old_status):
        pass
