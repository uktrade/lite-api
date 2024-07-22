from django.db.models import Q

from model_utils.managers import InheritanceManager

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class BaseApplicationManager(InheritanceManager):
    def drafts(self, organisation, sort_by):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().filter(status=draft, organisation=organisation).order_by(sort_by)

    def submitted(self, organisation, sort_by):
        finalised = get_case_status_by_status(CaseStatusEnum.FINALISED)
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return (
            self.get_queryset()
            .filter(organisation=organisation)
            .exclude(Q(status=draft) | Q(status=finalised))
            .order_by(sort_by)
        )

    def finalised(self, organisation, sort_by):
        finalised = get_case_status_by_status(CaseStatusEnum.FINALISED)
        return self.get_queryset().filter(status=finalised, organisation=organisation).order_by(sort_by)
