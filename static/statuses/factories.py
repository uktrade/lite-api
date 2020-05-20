import factory

from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus


class CaseStatusFactory(factory.django.DjangoModelFactory):
    status = CaseStatusEnum.SUBMITTED
    priority = 1

    class Meta:
        model = CaseStatus
