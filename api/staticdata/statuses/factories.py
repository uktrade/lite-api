import factory

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


class CaseStatusFactory(factory.django.DjangoModelFactory):
    status = CaseStatusEnum.SUBMITTED
    priority = 1

    class Meta:
        model = CaseStatus
