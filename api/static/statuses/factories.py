import factory

from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.models import CaseStatus


class CaseStatusFactory(factory.django.DjangoModelFactory):
    status = CaseStatusEnum.SUBMITTED
    priority = 1

    class Meta:
        model = CaseStatus
