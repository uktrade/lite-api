from model_utils.managers import InheritanceManager

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class BaseApplicationManager(InheritanceManager):
    def drafts(self, organisation):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().filter(status=draft, organisation=organisation).order_by("-created_at")

    def submitted(self, organisation, sort):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().filter(organisation=organisation).exclude(status=draft).order_by(sort)

    def finalised(self, organisation, sort):
        finalised = get_case_status_by_status(CaseStatusEnum.FINALISED)
        return self.get_queryset().filter(status=finalised, organisation=organisation).order_by(sort)
