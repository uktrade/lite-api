import factory

from faker import Faker

from api.applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from api.applications.models import (
    PartyOnApplication,
    CountryOnApplication,
    DenialMatchOnApplication,
    OpenApplication,
    SiteOnApplication,
    GoodOnApplication,
    StandardApplication,
)
from api.cases.enums import CaseTypeEnum
from api.external_data.models import Denial, SanctionMatch
from api.staticdata.countries.factories import CountryFactory
from api.staticdata.statuses.models import CaseStatus
from api.goods.tests.factories import GoodFactory
from api.organisations.tests.factories import OrganisationFactory, SiteFactory
from api.parties.tests.factories import PartyFactory
from api.users.tests.factories import ExporterUserFactory, GovUserFactory
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


faker = Faker()


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
    submitted_by = factory.SubFactory(ExporterUserFactory)

    class Meta:
        model = StandardApplication

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        if "status" in kwargs and isinstance(kwargs["status"], CaseStatus):
            obj.status = kwargs["status"]
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
    is_good_controlled = None

    @factory.post_generation
    def control_list_entries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        codes = extracted or []

        for code in codes:
            self.control_list_entries.add(get_control_list_entry(code))

    class Meta:
        model = GoodOnApplication


class DenialMatchFactory(factory.django.DjangoModelFactory):
    created_by = factory.SubFactory(GovUserFactory)
    reference = factory.LazyAttribute(lambda n: faker.uuid4())
    name = factory.LazyAttribute(lambda n: faker.name())
    address = factory.LazyAttribute(lambda n: faker.address())
    notifying_government = factory.LazyAttribute(lambda n: faker.country())
    country = factory.LazyAttribute(lambda n: faker.country())
    item_list_codes = factory.LazyAttribute(lambda n: faker.word())
    item_description = factory.LazyAttribute(lambda n: faker.sentence())
    consignee_name = factory.LazyAttribute(lambda n: faker.name())
    end_use = factory.LazyAttribute(lambda n: faker.sentence())

    class Meta:
        model = Denial


class DenialMatchOnApplicationFactory(factory.django.DjangoModelFactory):
    category = factory.Iterator(["partial", "exact"])
    application = factory.SubFactory(StandardApplicationFactory, organisation=factory.SelfAttribute("..organisation"))
    denial = factory.SubFactory(DenialMatchFactory)

    class Meta:
        model = DenialMatchOnApplication


class SanctionMatchFactory(factory.django.DjangoModelFactory):
    party_on_application = factory.SubFactory(PartyOnApplicationFactory)
    elasticsearch_reference = factory.LazyAttribute(lambda n: faker.word())
    name = factory.LazyAttribute(lambda n: faker.name())
    flag_uuid = factory.LazyAttribute(lambda n: faker.uuid4())
    is_revoked = factory.LazyAttribute(lambda n: faker.boolean())
    is_revoked_comment = factory.LazyAttribute(lambda n: faker.sentence())

    class Meta:
        model = SanctionMatch
