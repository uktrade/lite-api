import factory

from api.applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from api.applications.models import (
    PartyOnApplication,
    CountryOnApplication,
    OpenApplication,
    SiteOnApplication,
    GoodOnApplication,
    StandardApplication,
)
from api.cases.enums import CaseTypeEnum
from api.static.countries.factories import CountryFactory
from api.goods.tests.factories import GoodFactory
from api.organisations.tests.factories import OrganisationFactory, SiteFactory
from api.parties.tests.factories import PartyFactory
from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.libraries.get_case_status import get_case_status_by_status


class OpenApplicationFactory(factory.django.DjangoModelFactory):
    name = "Application Test Name"
    export_type = ApplicationExportType.PERMANENT
    case_type_id = CaseTypeEnum.SIEL.id
    activity = "Trade"
    usage = "Trade"
    organisation = factory.SubFactory(OrganisationFactory)
    is_military_end_use_controls = False
    is_informed_wmd = False
    is_suspected_wmd = False
    is_eu_military = False
    is_compliant_limitations_eu = None
    intended_end_use = "this is our intended end use"
    is_shipped_waybill_or_lading = True
    non_waybill_or_lading_route_details = None

    class Meta:
        model = OpenApplication

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        obj.save()
        return obj


class StandardApplicationFactory(factory.django.DjangoModelFactory):
    name = "Application Test Name"
    export_type = ApplicationExportType.PERMANENT
    case_type_id = CaseTypeEnum.SIEL.id
    have_you_been_informed = (ApplicationExportLicenceOfficialType.YES,)
    reference_number_on_information_form = ""
    activity = "Trade"
    usage = "Trade"
    organisation = factory.SubFactory(OrganisationFactory)
    is_military_end_use_controls = False
    is_informed_wmd = False
    is_suspected_wmd = False
    is_eu_military = False
    is_compliant_limitations_eu = None
    intended_end_use = "this is our intended end use"
    is_shipped_waybill_or_lading = True
    non_waybill_or_lading_route_details = None

    class Meta:
        model = StandardApplication

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        obj.save()
        return obj


class PartyOnApplicationFactory(factory.django.DjangoModelFactory):
    party = factory.SubFactory(PartyFactory)
    application = factory.SubFactory(StandardApplicationFactory)

    class Meta:
        model = PartyOnApplication


class CountryOnApplicationFactory(factory.django.DjangoModelFactory):
    application = factory.SubFactory(OpenApplicationFactory)
    country = factory.SubFactory(CountryFactory)

    class Meta:
        model = CountryOnApplication


class SiteOnApplicationFactory(factory.django.DjangoModelFactory):
    application = factory.SubFactory(StandardApplicationFactory, organisation=factory.SelfAttribute("..organisation"))
    site = factory.SubFactory(SiteFactory, organisation=factory.SelfAttribute("..organisation"))

    class Meta:
        model = SiteOnApplication

    class Params:
        organisation = factory.SubFactory(OrganisationFactory)


class GoodOnApplicationFactory(factory.django.DjangoModelFactory):
    application = factory.SubFactory(StandardApplicationFactory, organisation=factory.SelfAttribute("..organisation"))
    good = factory.SubFactory(GoodFactory, organisation=factory.SelfAttribute("..organisation"))

    class Meta:
        model = GoodOnApplication
