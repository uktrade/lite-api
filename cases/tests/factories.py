import factory

from addresses.tests.factories import AddressFactory
from applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.models import (
    StandardApplication,
    SiteOnApplication,
    GoodOnApplication,
    CountryOnApplication,
    PartyOnApplication,
    OpenApplication)
from cases.enums import AdviceLevel, AdviceType
from cases.enums import CaseTypeEnum
from cases.models import Advice
from goods.tests.factories import GoodFactory
from organisations.models import Site
from organisations.tests.factories import OrganisationFactory
from parties.enums import SubType, PartyType
from parties.models import Party
from static.countries.models import Country
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.enums import UserStatuses, UserType


class StandardApplicationFactory(factory.django.DjangoModelFactory):
    name = "Application Test Name"
    export_type = ApplicationExportType.PERMANENT
    case_type_id = CaseTypeEnum.SIEL.id
    have_you_been_informed = (ApplicationExportLicenceOfficialType.YES,)
    reference_number_on_information_form = ""
    activity = "Trade"
    usage = "Trade"
    organisation = factory.SubFactory(OrganisationFactory)
    status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
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


class OpenApplicationFactory(factory.django.DjangoModelFactory):
    name = "Application Test Name"
    export_type = ApplicationExportType.PERMANENT
    case_type_id = CaseTypeEnum.SIEL.id
    activity = "Trade"
    usage = "Trade"
    organisation = factory.SubFactory(OrganisationFactory)
    status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
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


class RoleFactory(factory.django.DjangoModelFactory):
    name = "fake_role"
    type = UserType.EXPORTER
    organisation = factory.SubFactory(OrganisationFactory)

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for permission in extracted:
                self.permissions.add(permission)

    @factory.post_generation
    def statuses(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for status in extracted:
                self.statuses.add(status)


class UserOrganisationRelationshipFactory(factory.django.DjangoModelFactory):
    organisation = factory.SubFactory(OrganisationFactory)
    role = factory.SubFactory(RoleFactory)
    status = UserStatuses.ACTIVE


class SiteFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    organisation = factory.SubFactory(OrganisationFactory)
    address = factory.SubFactory(AddressFactory)

    class Meta:
        model = Site

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user_organisation_relationship in extracted:
                self.users.add(user_organisation_relationship)


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


class CountryFactory(factory.django.DjangoModelFactory):
    id = factory.Iterator(["UK", "IT", "SP"])
    name = factory.Iterator(["United Kingdom", "Italy", "Spain"])
    is_eu = False
    type = factory.Iterator(["1", "2", "3"])

    class Meta:
        model = Country
        django_get_or_create = ("id",)


class CountryOnApplicationFactory(factory.django.DjangoModelFactory):
    application = factory.SubFactory(OpenApplicationFactory)
    country = factory.SubFactory(CountryFactory)

    class Meta:
        model = CountryOnApplication


class UserAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    level = AdviceLevel.USER

    class Meta:
        model = Advice


class TeamAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    level = AdviceLevel.TEAM

    class Meta:
        model = Advice


class FinalAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    level = AdviceLevel.FINAL

    class Meta:
        model = Advice


class PartyFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("address")
    name = factory.Faker("name")
    country = factory.SubFactory(CountryFactory)
    sub_type = SubType.OTHER
    type = PartyType.CONSIGNEE

    class Meta:
        model = Party


class PartyOnApplicationFactory(factory.django.DjangoModelFactory):
    party = factory.SubFactory(PartyFactory)
    application = factory.SubFactory(StandardApplicationFactory)

    class Meta:
        model = PartyOnApplication
