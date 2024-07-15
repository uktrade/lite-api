import factory

from faker import Faker

from api.applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from api.applications.models import (
    ApplicationDocument,
    ExternalLocationOnApplication,
    PartyOnApplication,
    DenialMatchOnApplication,
    SiteOnApplication,
    GoodOnApplication,
    GoodOnApplicationDocument,
    GoodOnApplicationInternalDocument,
    StandardApplication,
)
from api.cases.enums import CaseTypeEnum
from api.external_data.models import Denial, DenialEntity, SanctionMatch
from api.documents.tests.factories import DocumentFactory
from api.staticdata.statuses.models import CaseStatus
from api.goods.tests.factories import GoodFactory
from api.organisations.tests.factories import OrganisationFactory, SiteFactory, ExternalLocationFactory
from api.parties.tests.factories import ConsigneeFactory, EndUserFactory, PartyFactory, ThirdPartyFactory
from api.users.tests.factories import ExporterUserFactory, GovUserFactory
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from api.staticdata.regimes.helpers import get_regime_entry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


faker = Faker()


class StandardApplicationFactory(factory.django.DjangoModelFactory):
    name = "Application Test Name"
    export_type = ApplicationExportType.PERMANENT
    case_type_id = CaseTypeEnum.SIEL.id
    have_you_been_informed = ApplicationExportLicenceOfficialType.YES
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
    is_mod_security_approved = False
    goods_starting_point = StandardApplication.GB
    goods_recipients = StandardApplication.DIRECT_TO_END_USER
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


class SiteOnApplicationFactory(factory.django.DjangoModelFactory):
    application = factory.SubFactory(StandardApplicationFactory, organisation=factory.SelfAttribute("..organisation"))
    site = factory.SubFactory(SiteFactory, organisation=factory.SelfAttribute("..organisation"))

    class Meta:
        model = SiteOnApplication

    class Params:
        organisation = factory.SubFactory(OrganisationFactory)


class GoodOnApplicationFactory(factory.django.DjangoModelFactory):
    application = factory.SubFactory(StandardApplicationFactory)
    good = factory.SubFactory(GoodFactory)
    is_good_controlled = None

    @factory.post_generation
    def control_list_entries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        codes = extracted or []

        for code in codes:
            self.control_list_entries.add(get_control_list_entry(code))

    @factory.post_generation
    def regime_entries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        regime_entries = extracted or []
        for regime in regime_entries:
            self.regime_entries.add(get_regime_entry(regime))

    @factory.post_generation
    def report_summaries(self, create, extracted, **kwargs):
        if not create:
            return

        report_summaries = extracted or []
        self.report_summaries.set(report_summaries)

    class Meta:
        model = GoodOnApplication


class GoodOnApplicationDocumentFactory(DocumentFactory):
    application = factory.SubFactory(StandardApplicationFactory)
    good = factory.SubFactory(GoodFactory)
    user = factory.SubFactory(ExporterUserFactory)
    good_on_application = factory.SubFactory(
        GoodOnApplicationFactory,
        application=factory.SelfAttribute("..application"),
        good=factory.SelfAttribute("..good"),
    )

    class Meta:
        model = GoodOnApplicationDocument


class GoodOnApplicationInternalDocumentFactory(DocumentFactory):
    good_on_application = factory.SubFactory(GoodOnApplicationFactory)

    class Meta:
        model = GoodOnApplicationInternalDocument


class DenialFactory(factory.django.DjangoModelFactory):
    created_by_user = factory.SubFactory(GovUserFactory)
    reference = factory.LazyAttribute(lambda n: faker.uuid4())
    regime_reg_ref = factory.LazyAttribute(lambda n: faker.lexify(text="ABN/OREF-???????????"))
    notifying_government = factory.LazyAttribute(lambda n: faker.country())
    denial_cle = factory.LazyAttribute(lambda n: faker.word())
    item_description = factory.LazyAttribute(lambda n: faker.sentence())
    end_use = factory.LazyAttribute(lambda n: faker.sentence())

    class Meta:
        model = Denial


class DenialEntityFactory(factory.django.DjangoModelFactory):
    created_by = factory.SubFactory(GovUserFactory)
    name = factory.LazyAttribute(lambda n: faker.name())
    address = factory.LazyAttribute(lambda n: faker.address())
    country = factory.LazyAttribute(lambda n: faker.country())
    denial = factory.SubFactory(DenialFactory)

    class Meta:
        model = DenialEntity


class DenialMatchOnApplicationFactory(factory.django.DjangoModelFactory):
    category = factory.Iterator(["partial", "exact"])
    application = factory.SubFactory(StandardApplicationFactory, organisation=factory.SelfAttribute("..organisation"))
    denial_entity = factory.SubFactory(DenialEntityFactory)

    class Meta:
        model = DenialMatchOnApplication


class ApplicationDocumentFactory(DocumentFactory):
    application = factory.SubFactory(StandardApplicationFactory)

    class Meta:
        model = ApplicationDocument


class DenialExactMatchOnApplicationFactory(DenialMatchOnApplicationFactory):
    category = "exact"
    application = factory.SubFactory(StandardApplicationFactory)


class DenialPartialMatchOnApplicationFactory(DenialMatchOnApplicationFactory):
    category = "partial"
    application = factory.SubFactory(StandardApplicationFactory)


class ExternalLocationOnApplicationFactory(factory.django.DjangoModelFactory):
    application = factory.SubFactory(StandardApplicationFactory)
    external_location = factory.SubFactory(ExternalLocationFactory)

    class Meta:
        model = ExternalLocationOnApplication


class SanctionMatchFactory(factory.django.DjangoModelFactory):
    party_on_application = factory.SubFactory(PartyOnApplicationFactory)
    elasticsearch_reference = factory.LazyAttribute(lambda n: faker.word())
    name = factory.LazyAttribute(lambda n: faker.name())
    flag_uuid = factory.LazyAttribute(lambda n: faker.uuid4())
    is_revoked = factory.LazyAttribute(lambda n: faker.boolean())
    is_revoked_comment = factory.LazyAttribute(lambda n: faker.sentence())

    class Meta:
        model = SanctionMatch


class DraftStandardApplicationFactory(StandardApplicationFactory):
    goods_starting_point = StandardApplication.GB
    goods_recipients = StandardApplication.VIA_CONSIGNEE

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.status = get_case_status_by_status(CaseStatusEnum.DRAFT)
        obj.save()

        GoodOnApplicationFactory(application=obj, good=GoodFactory(organisation=obj.organisation))

        PartyOnApplicationFactory(application=obj, party=EndUserFactory(organisation=obj.organisation))

        if kwargs["goods_recipients"] in [
            StandardApplication.VIA_CONSIGNEE,
            StandardApplication.VIA_CONSIGNEE_AND_THIRD_PARTIES,
        ]:
            PartyOnApplicationFactory(application=obj, party=ConsigneeFactory(organisation=obj.organisation))

        if kwargs["goods_recipients"] == StandardApplication.VIA_CONSIGNEE_AND_THIRD_PARTIES:
            PartyOnApplicationFactory(application=obj, party=ThirdPartyFactory(organisation=obj.organisation))

        return obj
