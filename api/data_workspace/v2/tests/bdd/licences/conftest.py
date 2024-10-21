import pytest

from api.applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from api.cases.tests.factories import FinalAdviceFactory
from api.goods.tests.factories import GoodFactory
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import GoodOnLicenceFactory, StandardLicenceFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.units.enums import Units


@pytest.fixture()
def standard_draft_licence():
    application = StandardApplicationFactory(
        status=CaseStatus.objects.get(status=CaseStatusEnum.FINALISED),
    )
    good = GoodFactory(organisation=application.organisation)
    good_on_application = GoodOnApplicationFactory(
        application=application, good=good, quantity=100.0, value=1500, unit=Units.NAR
    )
    licence = StandardLicenceFactory(case=application, status=LicenceStatus.DRAFT)
    GoodOnLicenceFactory(
        good=good_on_application,
        quantity=good_on_application.quantity,
        usage=0.0,
        value=good_on_application.value,
        licence=licence,
    )
    return licence


@pytest.fixture()
def standard_licence():
    application = StandardApplicationFactory(
        status=CaseStatus.objects.get(status=CaseStatusEnum.FINALISED),
    )
    good = GoodFactory(organisation=application.organisation)
    good_on_application = GoodOnApplicationFactory(
        application=application, good=good, quantity=100.0, value=1500, unit=Units.NAR
    )
    licence = StandardLicenceFactory(case=application, status=LicenceStatus.DRAFT)
    GoodOnLicenceFactory(
        good=good_on_application,
        quantity=good_on_application.quantity,
        usage=0.0,
        value=good_on_application.value,
        licence=licence,
    )
    licence.status = LicenceStatus.ISSUED
    licence.save()
    return licence


@pytest.fixture()
def standard_case_with_final_advice(lu_case_officer):
    case = StandardApplicationFactory(
        status=CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW),
    )
    good = GoodFactory(organisation=case.organisation)
    good_on_application = GoodOnApplicationFactory(
        application=case, good=good, quantity=100.0, value=1500, unit=Units.NAR
    )
    FinalAdviceFactory(user=lu_case_officer, case=case, good=good_on_application.good)
    return case
