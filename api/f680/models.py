from django.db import models

from api.cases.enums import (
    CaseTypeSubTypeEnum,
    CaseTypeTypeEnum,
)
from api.cases.models import (
    CaseType,
)
from api.applications.models import BaseApplication
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class F680Application(BaseApplication):  # /PS-IGNORE
    data = models.JSONField()

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
