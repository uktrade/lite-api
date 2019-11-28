import uuid
from datetime import datetime, timezone

from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from addresses.models import Address
from applications.enums import (
    ApplicationType,
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
)
from applications.models import (
    BaseApplication,
    GoodOnApplication,
    SiteOnApplication,
    CountryOnApplication,
    StandardApplication,
    OpenApplication,
    HmrcQuery,
    ApplicationDocument,
)
from cases.enums import AdviceType, CaseType
from cases.models import (
    CaseNote,
    Case,
    CaseDocument,
    CaseAssignment,
    GoodCountryDecision,
)
from conf import settings
from conf.constants import Roles
from conf.urls import urlpatterns
from flags.models import Flag
from goods.enums import GoodControlled, GoodStatus
from goods.models import Good, GoodDocument
from goodstype.document.models import GoodsTypeDocument
from goodstype.models import GoodsType
from organisations.enums import OrganisationType
from organisations.models import Organisation, Site, ExternalLocation
from parties.document.models import PartyDocument
from parties.enums import SubType, PartyType, ThirdPartySubType
from parties.models import EndUser, UltimateEndUser, Consignee, ThirdParty, Party
from picklists.models import PicklistItem
from queries.control_list_classifications.models import ControlListClassificationQuery
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queues.models import Queue
from static.control_list_entries.models import ControlListEntry
from static.countries.helpers import get_country
from static.management.commands import seedall
from static.management.commands.seedall import SEED_COMMANDS
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from static.units.enums import Units
from static.urls import urlpatterns as static_urlpatterns
from teams.models import Team
from test_helpers import colours
from test_helpers.helpers import random_name
from users.enums import UserStatuses
from users.libraries.user_to_token import user_to_token
from users.models import ExporterUser, UserOrganisationRelationship, BaseUser, GovUser, Role


class Static:
    seeded = False


class DataTestClient(APITestCase, URLPatternsTestCase):
    """
    Test client which creates seeds the database with system data and sets up an initial organisation and user
    """

    urlpatterns = urlpatterns + static_urlpatterns
    client = APIClient

    @classmethod
    def setUpClass(cls):
        """ Run seed operations ONCE for the entire test suite. """
        if not Static.seeded:
            seedall.Command.seed_list(SEED_COMMANDS["Tests"])
            Static.seeded = True

    @classmethod
    def tearDownClass(cls):
        """ tearDownClass is required if `super()` isn't called within `setUpClass` """
        pass

    def setUp(self):
        # Gov User Setup
        self.team = Team.objects.get(name="Admin")
        self.gov_user = GovUser(email="test@mail.com", first_name="John", last_name="Smith", team=self.team)
        self.gov_user.save()
        self.gov_headers = {"HTTP_GOV_USER_TOKEN": user_to_token(self.gov_user)}

        # Exporter User Setup
        (self.organisation, self.exporter_user,) = self.create_organisation_with_exporter_user()
        (self.hmrc_organisation, self.hmrc_exporter_user,) = self.create_organisation_with_exporter_user(
            "HMRC org 5843", org_type=OrganisationType.HMRC
        )

        self.exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(self.exporter_user),
            "HTTP_ORGANISATION_ID": self.organisation.id,
        }

        self.default_role = Role.objects.get(id=Roles.INTERNAL_DEFAULT_ROLE_ID)
        self.super_user_role = Role.objects.get(id=Roles.INTERNAL_SUPER_USER_ROLE_ID)
        self.exporter_default_role = Role.objects.get(id=Roles.EXPORTER_DEFAULT_ROLE_ID)
        self.exporter_super_user_role = Role.objects.get(id=Roles.EXPORTER_SUPER_USER_ROLE_ID)

        self.hmrc_exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(self.hmrc_exporter_user),
            "HTTP_ORGANISATION_ID": self.hmrc_organisation.id,
        }

        self.queue = self.create_queue("Initial Queue", self.team)

        # Create a hardcoded control list entry rather than loading in the
        # spreadsheet each time
        ControlListEntry.create("ML1a", "Description", None, False)

        if settings.TIME_TESTS:
            self.tick = datetime.now()

    def tearDown(self):
        """
        Print output time for tests if settings.TIME_TESTS is set to True
        """
        if settings.TIME_TESTS:
            self.tock = datetime.now()

            diff = self.tock - self.tick
            time = round(diff.microseconds / 1000, 2)
            colour = colours.green
            emoji = ""

            if time > 100:
                colour = colours.orange
            if time > 300:
                colour = colours.red
                emoji = " 🔥"

            print(self._testMethodName + emoji + " " + colour(str(time) + "ms") + emoji)

    def get(self, path, data=None, follow=False, **extra):
        response = self.client.get(path, data, follow, **extra)
        return response.json(), response.status_code

    def create_exporter_user(self, organisation=None, first_name=None, last_name=None, role=None):
        if not first_name and not last_name:
            first_name, last_name = random_name()

        random_string = str(uuid.uuid4())

        exporter_user = ExporterUser(
            first_name=first_name, last_name=last_name, email=f"{first_name}.{last_name}@{random_string}.com",
        )
        exporter_user.organisation = organisation
        exporter_user.save()

        if organisation:
            if not role:
                role = Role.objects.get(id=Roles.EXPORTER_DEFAULT_ROLE_ID)
            UserOrganisationRelationship(user=exporter_user, organisation=organisation, role=role).save()
            exporter_user.status = UserStatuses.ACTIVE

        return exporter_user

    @staticmethod
    def add_exporter_user_to_org(organisation, exporter_user, role=None):
        if not role:
            role = Role.objects.get(id=Roles.EXPORTER_DEFAULT_ROLE_ID)
        UserOrganisationRelationship(user=exporter_user, organisation=organisation, role=role).save()

    @staticmethod
    def create_site(name, org, country="GB"):
        address = Address(
            address_line_1="42 Road",
            address_line_2="",
            country=get_country(country),
            city="London",
            region="Buckinghamshire",
            postcode="E14QW",
        )
        address.save()
        site = Site(name=name, organisation=org, address=address)
        site.save()
        return site, address

    @staticmethod
    def create_external_location(name, org, country="GB"):
        external_location = ExternalLocation(
            name=name, address="20 Questions Road, Enigma", country=get_country(country), organisation=org,
        )
        external_location.save()
        return external_location

    @staticmethod
    def create_end_user(name, organisation):
        end_user = EndUser(
            name=name,
            organisation=organisation,
            address="42 Road, London, Buckinghamshire",
            website="www." + name + ".com",
            sub_type=SubType.GOVERNMENT,
            type=PartyType.END,
            country=get_country("GB"),
        )
        end_user.save()
        return end_user

    @staticmethod
    def create_ultimate_end_user(name, organisation):
        ultimate_end_user = UltimateEndUser(
            name=name,
            organisation=organisation,
            address="42 Road, London, Buckinghamshire",
            website="www." + name + ".com",
            sub_type=SubType.GOVERNMENT,
            type=PartyType.ULTIMATE,
            country=get_country("GB"),
        )
        ultimate_end_user.save()
        return ultimate_end_user

    @staticmethod
    def create_consignee(name, organisation):
        consignee = Consignee(
            name=name,
            organisation=organisation,
            address="42 Road, London, Buckinghamshire",
            website="www." + name + ".com",
            sub_type=SubType.GOVERNMENT,
            type=PartyType.CONSIGNEE,
            country=get_country("GB"),
        )
        consignee.save()
        return consignee

    @staticmethod
    def create_third_party(name, organisation):
        third_party = ThirdParty(
            name=name,
            organisation=organisation,
            address="42 Road, London, Buckinghamshire",
            website="www." + name + ".com",
            sub_type=ThirdPartySubType.AGENT,
            type=PartyType.THIRD,
            country=get_country("GB"),
        )
        third_party.save()
        return third_party

    @staticmethod
    def create_case_note(
        case: Case, text: str, user: BaseUser, is_visible_to_exporter: bool = False,
    ):
        case_note = CaseNote(case=case, text=text, user=user, is_visible_to_exporter=is_visible_to_exporter,)
        case_note.save()
        return case_note

    @staticmethod
    def create_queue(name: str, team: Team):
        queue = Queue(name=name, team=team)
        queue.save()
        return queue

    @staticmethod
    def create_gov_user(email: str, team: Team):
        gov_user = GovUser(email=email, team=team)
        gov_user.save()
        return gov_user

    @staticmethod
    def create_team(name: str):
        team = Team(name=name)
        team.save()
        return team

    @staticmethod
    def submit_application(application: BaseApplication):
        application.submitted_at = datetime.now(timezone.utc)
        application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        application.save()

        if application.application_type == ApplicationType.STANDARD_LICENCE:
            for good_on_application in GoodOnApplication.objects.filter(application=application):
                good_on_application.good.status = GoodStatus.SUBMITTED
                good_on_application.good.save()

        return application

    @staticmethod
    def create_case_document(case: Case, user: GovUser, name: str):
        case_doc = CaseDocument(
            case=case,
            description="This is a document",
            user=user,
            name=name,
            s3_key="thisisakey",
            size=123456,
            virus_scanned_at=None,
            safe=None,
        )
        case_doc.save()
        return case_doc

    @staticmethod
    def create_application_document(application):
        application_doc = ApplicationDocument(
            application=application,
            description="document description",
            name="document name",
            s3_key="documentkey",
            size=12,
            virus_scanned_at=None,
            safe=None,
        )

        application_doc.save()
        return application_doc

    @staticmethod
    def create_good_document(
        good: Good, user: ExporterUser, organisation: Organisation, name: str, s3_key: str,
    ):
        good_doc = GoodDocument(
            good=good,
            description="This is a document",
            user=user,
            organisation=organisation,
            name=name,
            s3_key=s3_key,
            size=123456,
            virus_scanned_at=None,
            safe=None,
        )
        good_doc.save()
        return good_doc

    @staticmethod
    def create_document_for_party(party: Party, name="document_name.pdf", safe=True):
        document = PartyDocument(
            party=party, name=name, s3_key="s3_keykey.pdf", size=123456, virus_scanned_at=None, safe=safe,
        )
        document.save()
        return document

    @staticmethod
    def create_document_for_goods_type(goods_type: GoodsType, name="document_name.pdf", safe=True):
        document = GoodsTypeDocument(
            goods_type=goods_type, name=name, s3_key="s3_keykey.pdf", size=123456, virus_scanned_at=None, safe=safe,
        )
        document.save()
        return document

    @staticmethod
    def create_flag(name: str, level: str, team: Team):
        flag = Flag(name=name, level=level, team=team)
        flag.save()
        return flag

    @staticmethod
    def create_case_assignment(queue, case, users):
        case_assignment = CaseAssignment(queue=queue, case=case)
        case_assignment.users.set(users)
        case_assignment.save()
        return case_assignment

    @staticmethod
    def create_goods_type(application):
        goods_type = GoodsType(
            description="thing",
            is_good_controlled=False,
            control_code="ML1a",
            is_good_end_product=True,
            application=application,
        )
        goods_type.save()
        return goods_type

    @staticmethod
    def create_picklist_item(name, team: Team, picklist_type, status):
        picklist_item = PicklistItem(
            team=team,
            name=name,
            text="This is a string of text, please do not disturb the milk argument",
            type=picklist_type,
            status=status,
        )
        picklist_item.save()
        return picklist_item

    @staticmethod
    def create_controlled_good(description: str, org: Organisation, control_code: str = "ML1") -> Good:
        good = Good(
            description=description,
            is_good_controlled=GoodControlled.YES,
            control_code=control_code,
            is_good_end_product=True,
            part_number="123456",
            organisation=org,
        )
        good.save()
        return good

    @staticmethod
    def create_clc_query(description, organisation):
        good = Good(
            description=description,
            is_good_controlled=GoodControlled.UNSURE,
            control_code="ML1",
            is_good_end_product=True,
            part_number="123456",
            organisation=organisation,
            comment=None,
            report_summary=None,
        )
        good.save()

        clc_query = ControlListClassificationQuery.objects.create(
            details="this is a test text",
            good=good,
            organisation=organisation,
            type=CaseType.CLC_QUERY,
            status=get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )
        return clc_query

    @staticmethod
    def create_advice(user, case, advice_field, advice_type, advice_level):
        advice = advice_level(
            user=user, case=case, type=advice_type, note="This is a note to the exporter", text="This is some text",
        )

        advice.team = user.team
        advice.save()

        if advice_field == "end_user":
            advice.end_user = StandardApplication.objects.get(pk=case.id).end_user

        if advice_field == "good":
            advice.good = GoodOnApplication.objects.get(application=case).good

        if advice_type == AdviceType.PROVISO:
            advice.proviso = "I am easy to proviso"

        if advice_type == AdviceType.REFUSE:
            advice.denial_reasons.set(["1a", "1b", "1c"])

        advice.save()
        return advice

    @staticmethod
    def create_good_country_decision(case, goods_type, country, decision):
        GoodCountryDecision(case=case, good=goods_type, country=country, decision=decision).save()

    def get(self, path, data=None, follow=False, **extra):
        response = self.client.get(path, data, follow, **extra)
        return response.json(), response.status_code

    def create_organisation_with_exporter_user(self, name="Organisation", org_type=None):
        organisation = Organisation(
            name=name,
            eori_number="GB123456789000",
            sic_number="2765",
            vat_number="123456789",
            registration_number="987654321",
        )
        if org_type:
            organisation.type = org_type
        organisation.save()

        site, address = self.create_site("HQ", organisation)

        organisation.primary_site = site
        organisation.save()

        exporter_user = self.create_exporter_user(organisation)

        return organisation, exporter_user

    def create_standard_application(
        self, organisation: Organisation, reference_name="Standard Draft", safe_document=True,
    ):
        application = StandardApplication(
            name=reference_name,
            application_type=ApplicationType.STANDARD_LICENCE,
            export_type=ApplicationExportType.PERMANENT,
            have_you_been_informed=ApplicationExportLicenceOfficialType.YES,
            reference_number_on_information_form="",
            activity="Trade",
            usage="Trade",
            organisation=organisation,
            end_user=self.create_end_user("End User", organisation),
            consignee=self.create_consignee("Consignee", organisation),
            type=CaseType.APPLICATION,
        )

        application.save()
        application.third_parties.set([self.create_third_party("Third party", self.organisation)])
        application.save()

        # Add a good to the standard application
        self.good_on_application = GoodOnApplication(
            good=self.create_controlled_good("a thing", organisation),
            application=application,
            quantity=10,
            unit=Units.NAR,
            value=500,
        )

        self.good_on_application.save()

        # Set the application party documents
        self.create_document_for_party(application.end_user, safe=safe_document)
        self.create_document_for_party(application.consignee, safe=safe_document)
        self.create_document_for_party(application.third_parties.first(), safe=safe_document)
        self.create_application_document(application)

        # Add a site to the application
        SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_standard_application_with_incorporated_good(
        self, organisation: Organisation, reference_name="Standard Draft", safe_document=True,
    ):

        application = self.create_standard_application(organisation, reference_name, safe_document)

        part_good = Good(
            is_good_end_product=False,
            is_good_controlled=True,
            control_code="ML17",
            organisation=self.organisation,
            description="a good",
            part_number="123456",
        )
        part_good.save()

        GoodOnApplication(good=part_good, application=application, quantity=17, value=18).save()

        application.ultimate_end_users.set([self.create_ultimate_end_user("Ultimate End User", self.organisation)])
        self.create_document_for_party(application.ultimate_end_users.first(), safe=safe_document)

        return application

    def create_open_application(self, organisation: Organisation, reference_name="Open Draft"):
        application = OpenApplication(
            name=reference_name,
            application_type=ApplicationType.OPEN_LICENCE,
            export_type=ApplicationExportType.PERMANENT,
            activity="Trade",
            usage="Trade",
            organisation=organisation,
        )

        application.save()

        # Add a goods description
        self.create_goods_type(application)
        self.create_goods_type(application)

        # Add a country to the application
        CountryOnApplication(application=application, country=get_country("GB")).save()

        # Add a site to the application
        SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_hmrc_query(
        self, organisation: Organisation, reference_name="HMRC Query", safe_document=True,
    ):
        application = HmrcQuery(
            name=reference_name,
            application_type=ApplicationType.HMRC_QUERY,
            activity="Trade",
            usage="Trade",
            organisation=organisation,
            hmrc_organisation=self.hmrc_organisation,
            end_user=self.create_end_user("End User", organisation),
            consignee=self.create_consignee("Consignee", organisation),
            reasoning="I Am Easy to Find",
            type=CaseType.HMRC_QUERY,
        )

        application.save()

        application.third_parties.set([self.create_third_party("Third party", self.organisation)])

        goods_type = self.create_goods_type(application)

        # Set the application party documents
        self.create_document_for_party(application.end_user, safe=safe_document)
        self.create_document_for_party(application.consignee, safe=safe_document)
        self.create_document_for_party(application.third_parties.first(), safe=safe_document)

        self.create_document_for_goods_type(goods_type)

        # Add a site to the application
        SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_standard_application_case(self, organisation: Organisation, reference_name="Standard Application Case"):
        """
        Creates a complete standard application case
        """
        draft = self.create_standard_application(organisation, reference_name)

        return self.submit_application(draft)

    def create_end_user_advisory(self, note: str, reasoning: str, organisation: Organisation):
        end_user = self.create_end_user("name", self.organisation)
        end_user_advisory_query = EndUserAdvisoryQuery.objects.create(
            end_user=end_user,
            note=note,
            reasoning=reasoning,
            organisation=organisation,
            contact_telephone="1234567890",
            contact_name="Joe",
            contact_email="joe@something.com",
            contact_job_title="director",
            nature_of_business="guns",
            status=get_case_status_by_status(CaseStatusEnum.SUBMITTED),
            type=CaseType.END_USER_ADVISORY_QUERY,
        )
        end_user_advisory_query.save()
        return end_user_advisory_query

    def create_end_user_advisory_case(self, note: str, reasoning: str, organisation: Organisation):
        return self.create_end_user_advisory(note, reasoning, organisation)
