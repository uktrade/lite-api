import factory

from django.utils import timezone

from api.cases.enums import CaseTypeEnum
from api.organisations.tests.factories import OrganisationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status

from api.f680.models import F680Application  # /PS-IGNORE


class F680ApplicationFactory(factory.django.DjangoModelFactory):  # /PS-IGNORE
    class Meta:
        model = F680Application  # /PS-IGNORE

    application = {"some": "json"}
    case_type_id = CaseTypeEnum.F680.id
    organisation = factory.SubFactory(OrganisationFactory)
    status = factory.LazyAttribute(lambda o: get_case_status_by_status(CaseStatusEnum.DRAFT))


class SubmittedF680ApplicationFactory(F680ApplicationFactory):  # /PS-IGNORE
    status = factory.LazyAttribute(lambda o: get_case_status_by_status(CaseStatusEnum.SUBMITTED))
    submitted_at = factory.LazyFunction(timezone.now)
