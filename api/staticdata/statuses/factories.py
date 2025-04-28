import factory

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import (
    CaseStatus,
    CaseSubStatus,
)


class CaseStatusFactory(factory.django.DjangoModelFactory):
    status = CaseStatusEnum.SUBMITTED
    priority = 1

    class Meta:
        model = CaseStatus
        django_get_or_create = ("status",)


class CaseSubStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CaseSubStatus
        django_get_or_create = ("id",)
