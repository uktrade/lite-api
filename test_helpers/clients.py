import uuid
from datetime import datetime, timezone

import django.utils.timezone
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from addresses.models import Address
from applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.libraries.goods_on_applications import update_submitted_application_good_statuses_and_flags
from applications.libraries.licence import get_default_duration
from applications.models import (
    BaseApplication,
    GoodOnApplication,
    SiteOnApplication,
    CountryOnApplication,
    StandardApplication,
    OpenApplication,
    HmrcQuery,
    ApplicationDocument,
    ExhibitionClearanceApplication,
    GiftingClearanceApplication,
    F680ClearanceApplication,
    Licence,
)
from cases.enums import AdviceType, CaseDocumentState, CaseTypeEnum
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseNote, Case, CaseDocument, CaseAssignment, GoodCountryDecision, EcjuQuery
from cases.sla import get_application_target_sla
from conf import settings
from conf.constants import Roles
from conf.urls import urlpatterns
from flags.enums import SystemFlags, FlagStatuses
from flags.models import Flag, FlaggingRule
from goods.enums import GoodControlled, GoodPvGraded, PvGrading
from goods.models import Good, GoodDocument, PvGradingDetails
from goodstype.document.models import GoodsTypeDocument
from goodstype.models import GoodsType
from letter_templates.models import LetterTemplate
from organisations.enums import OrganisationType, OrganisationStatus
from organisations.models import Organisation, Site, ExternalLocation
from parties.enums import SubType, PartyType, PartyRole
from parties.models import Party
from parties.models import PartyDocument
from picklists.enums import PickListStatus, PicklistType
from picklists.models import PicklistItem
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queries.goods_query.models import GoodsQuery
from queues.models import Queue
from static.control_list_entries.models import ControlListEntry
from static.countries.helpers import get_country
from static.f680_clearance_types.models import F680ClearanceType
from static.letter_layouts.models import LetterLayout
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
        (self.organisation, self.exporter_user) = self.create_organisation_with_exporter_user()
        (self.hmrc_organisation, self.hmrc_exporter_user) = self.create_organisation_with_exporter_user(
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
        if settings.SUPPRESS_TEST_OUTPUT:
            pass
        elif settings.TIME_TESTS:
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

    def assertEqualIgnoreType(self, first, second, msg=None):
        """Fail if the two objects (as strings) are unequal as determined by the '=='
           operator.
        """
        first = str(first)
        second = str(second)
        assertion_func = self._getAssertEqualityFunc(first, second)
        assertion_func(first, second, msg=msg)

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
        return site

    @staticmethod
    def create_external_location(name, org, country="GB"):
        external_location = ExternalLocation(
            name=name, address="20 Questions Road, Enigma", country=get_country(country), organisation=org,
        )
        external_location.save()
        return external_location

    @staticmethod
    def create_party(name, organisation, party_type, application=None, pk=None):
        if not pk:
            pk = uuid.uuid4()

        data = {
            "id": pk,
            "name": name,
            "organisation": organisation,
            "address": "42 Road, London, Buckinghamshire",
            "website": "www." + name + ".com",
            "sub_type": SubType.GOVERNMENT,
            "type": party_type,
            "country": get_country("GB"),
        }

        if party_type == PartyType.THIRD_PARTY:
            data["role"] = PartyRole.AGENT

        party = Party(**data)
        party.save()

        if application:
            # Attach party to application
            application.add_party(party)
        return party

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
        application.sla_remaining_days = get_application_target_sla(application.case_type.sub_type)
        application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        application.save()

        update_submitted_application_good_statuses_and_flags(application)

        return application

    @staticmethod
    def create_case_document(case: Case, user: GovUser, name: str, visible_to_exporter=True):
        case_doc = CaseDocument(
            case=case,
            description="This is a document",
            user=user,
            name=name,
            s3_key="thisisakey",
            size=123456,
            virus_scanned_at=None,
            safe=None,
            visible_to_exporter=visible_to_exporter,
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
    def create_flagging_rule(
        level: str, team: Team, flag: Flag, matching_value: str, status: str = FlagStatuses.ACTIVE
    ):
        flagging_rule = FlaggingRule(level=level, team=team, flag=flag, matching_value=matching_value, status=status)
        flagging_rule.save()
        return flagging_rule

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
            is_good_incorporated=True,
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
    def create_good(
        description: str,
        org: Organisation,
        is_good_controlled: str = GoodControlled.YES,
        control_code: str = "ML1X",
        is_pv_graded: str = GoodPvGraded.YES,
        pv_grading_details: PvGradingDetails = None,
    ) -> Good:
        if is_pv_graded == GoodPvGraded.YES and not pv_grading_details:
            pv_grading_details = PvGradingDetails.objects.create(
                grading=None,
                custom_grading="Custom Grading",
                prefix="Prefix",
                suffix="Suffix",
                issuing_authority="Issuing Authority",
                reference="ref123",
                date_of_issue="2019-12-25",
            )

        good = Good(
            description=description,
            is_good_controlled=is_good_controlled,
            control_code=control_code,
            part_number="123456",
            organisation=org,
            comment=None,
            report_summary=None,
            is_pv_graded=is_pv_graded,
            pv_grading_details=pv_grading_details,
        )
        good.save()
        return good

    @staticmethod
    def create_clc_query(description, organisation) -> GoodsQuery:
        good = DataTestClient.create_good(description=description, org=organisation, is_pv_graded=GoodPvGraded.NO)

        clc_query = GoodsQuery.objects.create(
            clc_raised_reasons="this is a test text",
            good=good,
            organisation=organisation,
            case_type_id=CaseTypeEnum.GOODS.id,
            status=get_case_status_by_status(CaseStatusEnum.SUBMITTED),
            submitted_at=django.utils.timezone.now(),
        )
        clc_query.flags.add(Flag.objects.get(id=SystemFlags.GOOD_CLC_QUERY_ID))
        clc_query.save()
        return clc_query

    @staticmethod
    def create_pv_grading_query(description, organisation) -> GoodsQuery:
        good = DataTestClient.create_good(
            description=description, org=organisation, is_pv_graded=GoodPvGraded.GRADING_REQUIRED,
        )

        pv_grading_query = GoodsQuery.objects.create(
            clc_raised_reasons=None,
            pv_grading_raised_reasons="this is a test text",
            good=good,
            organisation=organisation,
            case_type_id=CaseTypeEnum.GOODS.id,
            status=get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )
        pv_grading_query.flags.add(Flag.objects.get(id=SystemFlags.GOOD_PV_GRADING_QUERY_ID))
        pv_grading_query.save()
        return pv_grading_query

    @staticmethod
    def create_advice(user, case, advice_field, advice_type, advice_level, pv_grading=None):
        advice = advice_level(
            user=user,
            case=case,
            type=advice_type,
            note="This is a note to the exporter",
            text="This is some text",
            pv_grading=pv_grading,
        )

        advice.team = user.team
        advice.save()

        if advice_field == "end_user":
            advice.end_user = StandardApplication.objects.get(pk=case.id).end_user.party

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
            status=OrganisationStatus.ACTIVE,
        )
        if org_type:
            organisation.type = org_type
        organisation.save()

        site = self.create_site("HQ", organisation)

        organisation.primary_site = site
        organisation.save()

        exporter_user = self.create_exporter_user(organisation)

        return organisation, exporter_user

    def add_party_documents(self, application, safe_document, consignee=True):
        # Set the application party documents
        self.create_document_for_party(application.end_user.party, safe=safe_document)
        if consignee:
            self.create_document_for_party(application.consignee.party, safe=safe_document)
        self.create_document_for_party(application.third_parties.first().party, safe=safe_document)

    def create_draft_standard_application(
        self,
        organisation: Organisation,
        reference_name="Standard Draft",
        safe_document=True,
        case_type_id=CaseTypeEnum.SIEL.id,
    ):
        application = StandardApplication(
            name=reference_name,
            export_type=ApplicationExportType.PERMANENT,
            case_type_id=case_type_id,
            have_you_been_informed=ApplicationExportLicenceOfficialType.YES,
            reference_number_on_information_form="",
            activity="Trade",
            usage="Trade",
            organisation=organisation,
            status=get_case_status_by_status(CaseStatusEnum.DRAFT),
            is_military_end_use_controls=False,
            is_informed_wmd=False,
            is_suspected_wmd=False,
            is_eu_military=False,
            is_compliant_limitations_eu=None,
        )

        application.save()

        # Add a good to the standard application
        self.good_on_application = GoodOnApplication(
            good=self.create_good("a thing", organisation),
            application=application,
            quantity=10,
            unit=Units.NAR,
            value=500,
        )

        self.good_on_application.save()
        self.create_party("End User", organisation, PartyType.END_USER, application)
        self.create_party("Consignee", organisation, PartyType.CONSIGNEE, application)
        self.create_party("Third party", organisation, PartyType.THIRD_PARTY, application)
        # Set the application party documents

        self.add_party_documents(application, safe_document)

        self.create_application_document(application)

        # Add a site to the application
        SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_mod_clearance_application(
        self, organisation, case_type, reference_name="MOD Clearance Draft", safe_document=True,
    ):
        if case_type == CaseTypeEnum.F680:
            model = F680ClearanceApplication
        elif case_type == CaseTypeEnum.GIFTING:
            model = GiftingClearanceApplication
        elif case_type == CaseTypeEnum.EXHIBITION:
            model = ExhibitionClearanceApplication
        else:
            raise BaseException("Invalid case type when creating test MOD Clearance application")

        application = model.objects.create(
            name=reference_name,
            activity="Trade",
            usage="Trade",
            organisation=organisation,
            case_type_id=case_type.id,
            status=get_case_status_by_status(CaseStatusEnum.DRAFT),
            clearance_level=PvGrading.UK_UNCLASSIFIED if case_type == CaseTypeEnum.F680 else None,
        )

        if case_type == CaseTypeEnum.EXHIBITION:
            application.title = "title"
            application.required_by_date = "2021-07-20"
            application.first_exhibition_date = "2022-08-19"
            application.save()
            # must be refreshed to return data in same format as database call
            application.refresh_from_db()
        elif case_type == CaseTypeEnum.F680:
            application.types.add(F680ClearanceType.objects.first())
            self.create_party("End User", organisation, PartyType.END_USER, application)
            self.create_party("Third party", organisation, PartyType.THIRD_PARTY, application)
            self.add_party_documents(application, safe_document, consignee=case_type == CaseTypeEnum.EXHIBITION)
        else:
            self.create_party("End User", organisation, PartyType.END_USER, application)
            self.create_party("Third party", organisation, PartyType.THIRD_PARTY, application)
            self.add_party_documents(application, safe_document, consignee=case_type == CaseTypeEnum.EXHIBITION)

        if case_type not in [CaseTypeEnum.F680, CaseTypeEnum.EXHIBITION, CaseTypeEnum.GIFTING]:
            self.create_party("Consignee", organisation, PartyType.CONSIGNEE, application)

        # Add a good to the standard application
        self.good_on_application = GoodOnApplication.objects.create(
            good=self.create_good("a thing", organisation),
            application=application,
            quantity=10,
            unit=Units.NAR,
            value=500,
        )

        self.create_application_document(application)

        if case_type == CaseTypeEnum.EXHIBITION:
            # Add a site to the application
            SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_incorporated_good_and_ultimate_end_user_on_application(self, organisation, application):
        good = Good.objects.create(
            is_good_controlled=True,
            control_code="ML17",
            organisation=self.organisation,
            description="a good",
            part_number="123456",
        )

        GoodOnApplication.objects.create(
            good=good, application=application, quantity=17, value=18, is_good_incorporated=True
        )

        self.ultimate_end_user = self.create_party(
            "Ultimate End User", organisation, PartyType.ULTIMATE_END_USER, application
        )
        self.create_document_for_party(application.ultimate_end_users.first().party, safe=True)

        return application

    def create_standard_application_with_incorporated_good(
        self, organisation: Organisation, reference_name="Standard Draft", safe_document=True,
    ):

        application = self.create_draft_standard_application(organisation, reference_name, safe_document)

        part_good = Good(
            is_good_controlled=GoodControlled.YES,
            control_code="ML17",
            organisation=self.organisation,
            description="a good",
            part_number="123456",
        )
        part_good.save()

        GoodOnApplication(
            good=part_good, application=application, quantity=17, value=18, is_good_incorporated=True
        ).save()

        self.ultimate_end_user = self.create_party(
            "Ultimate End User", organisation, PartyType.ULTIMATE_END_USER, application
        )
        self.create_document_for_party(application.ultimate_end_users.first().party, safe=safe_document)

        return application

    def create_draft_open_application(self, organisation: Organisation, reference_name="Open Draft"):
        application = OpenApplication(
            name=reference_name,
            case_type_id=CaseTypeEnum.OIEL.id,
            export_type=ApplicationExportType.PERMANENT,
            activity="Trade",
            usage="Trade",
            organisation=organisation,
            status=get_case_status_by_status(CaseStatusEnum.DRAFT),
            is_military_end_use_controls=False,
            is_informed_wmd=False,
            is_suspected_wmd=False,
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
            case_type_id=CaseTypeEnum.HMRC.id,
            activity="Trade",
            usage="Trade",
            organisation=organisation,
            hmrc_organisation=self.hmrc_organisation,
            reasoning="I Am Easy to Find",
            status=get_case_status_by_status(CaseStatusEnum.DRAFT),
        )
        application.save()

        end_user = self.create_party("End User", organisation, PartyType.END_USER, application)
        consignee = self.create_party("Consignee", organisation, PartyType.CONSIGNEE, application)
        third_party = self.create_party("Third party", organisation, PartyType.THIRD_PARTY, application)

        self.assertEqual(end_user, application.end_user.party)
        self.assertEqual(consignee, application.consignee.party)
        self.assertEqual(third_party, application.third_parties.get().party)

        goods_type = self.create_goods_type(application)

        # Set the application party documents
        self.create_document_for_party(application.end_user.party, safe=safe_document)
        self.create_document_for_party(application.consignee.party, safe=safe_document)
        self.create_document_for_party(application.third_parties.first().party, safe=safe_document)

        self.create_document_for_goods_type(goods_type)

        # Add a site to the application
        SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_standard_application_case(self, organisation: Organisation, reference_name="Standard Application Case"):
        """
        Creates a complete standard application case
        """
        draft = self.create_draft_standard_application(organisation, reference_name)

        return self.submit_application(draft)

    def create_end_user_advisory(self, note: str, reasoning: str, organisation: Organisation):
        end_user = self.create_party("name", self.organisation, PartyType.END_USER)
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
            case_type_id=CaseTypeEnum.EUA.id,
        )
        end_user_advisory_query.save()
        return end_user_advisory_query

    def create_end_user_advisory_case(self, note: str, reasoning: str, organisation: Organisation):
        return self.create_end_user_advisory(note, reasoning, organisation)

    def create_generated_case_document(
        self, case, template, visible_to_exporter=True, document_name="Generated Doc", advice_type=None
    ):
        generated_case_doc = GeneratedCaseDocument.objects.create(
            name=document_name,
            user=self.gov_user,
            s3_key=uuid.uuid4(),
            virus_scanned_at=datetime.now(timezone.utc),
            safe=True,
            type=CaseDocumentState.GENERATED,
            case=case,
            template=template,
            text="Here is some text",
            visible_to_exporter=visible_to_exporter,
            advice_type=advice_type,
        )
        return generated_case_doc

    def create_letter_template(self, name=None, case_type=CaseTypeEnum.case_type_list[0].id, decisions=None):
        if not name:
            name = str(uuid.uuid4())[0:35]

        picklist_item = self.create_picklist_item("#1", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE)
        letter_layout = LetterLayout.objects.first()

        letter_template = LetterTemplate.objects.create(name=name, layout=letter_layout)
        if decisions:
            letter_template.decisions.set(decisions)
        letter_template.case_types.add(case_type)
        letter_template.letter_paragraphs.add(picklist_item)
        letter_template.save()

        return letter_template

    def create_ecju_query(self, case, question="ECJU question", gov_user=None):
        ecju_query = EcjuQuery(case=case, question=question, raised_by_user=gov_user if gov_user else self.gov_user)
        ecju_query.save()
        return ecju_query

    @staticmethod
    def create_licence(application: BaseApplication, is_complete: bool):
        return Licence.objects.create(
            application=application,
            start_date=django.utils.timezone.now().date(),
            duration=get_default_duration(application),
            is_complete=is_complete,
        )
