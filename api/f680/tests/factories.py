import factory

from api.cases.enums import CaseTypeEnum
from api.organisations.tests.factories import OrganisationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status

from api.f680.models import F680Application  # /PS-IGNORE


class F680ApplicationFactory(factory.django.DjangoModelFactory):  # /PS-IGNORE
    class Meta:
        model = F680Application  # /PS-IGNORE

    case_type_id = CaseTypeEnum.F680.id
    organisation = factory.SubFactory(OrganisationFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        if "status" not in kwargs:
            obj.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        if "application" not in kwargs:
            obj.application = {"some": "json"}

        obj.save()
        return obj
