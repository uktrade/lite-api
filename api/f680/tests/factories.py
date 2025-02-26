import factory

from django.utils import timezone

from api.cases.enums import CaseTypeEnum
from api.cases.tests.factories import LazyStatus
from api.organisations.tests.factories import OrganisationFactory
from api.staticdata.statuses.enums import CaseStatusEnum

from api.f680.models import F680Application


class F680ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = F680Application

    application = {"some": "json"}
    case_type_id = CaseTypeEnum.F680.id
    organisation = factory.SubFactory(OrganisationFactory)
    status = LazyStatus(CaseStatusEnum.DRAFT)


class SubmittedF680ApplicationFactory(F680ApplicationFactory):
    status = LazyStatus(CaseStatusEnum.SUBMITTED)
    submitted_at = factory.LazyFunction(timezone.now)
