import timeit
import uuid
import warnings
from datetime import datetime, timezone
from typing import Optional, List

import django.utils.timezone
from django.conf import settings as conf_settings
from django.db import connection
from django.test import tag
from faker import Faker
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.libraries.edit_applications import set_case_flags_on_submitted_standard_or_open_application
from applications.libraries.goods_on_applications import add_goods_flags_to_submitted_application
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
)
from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from cases.enums import AdviceType, CaseDocumentState, CaseTypeEnum, CaseTypeSubTypeEnum
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseNote, Case, CaseDocument, CaseAssignment, GoodCountryDecision, EcjuQuery, CaseType, Advice
from cases.tasks import get_application_target_sla
from conf import settings
from conf.constants import Roles
from conf.urls import urlpatterns
from flags.enums import SystemFlags, FlagStatuses, FlagLevels
from flags.models import Flag, FlaggingRule
from flags.tests.factories import FlagFactory
from goods.enums import GoodControlled, GoodPvGraded, PvGrading, ItemCategory, MilitaryUse, Component, FirearmGoodType
from goods.models import Good, GoodDocument, PvGradingDetails, FirearmGoodDetails
from goods.tests.factories import GoodFactory
from goodstype.document.models import GoodsTypeDocument
from goodstype.models import GoodsType
from goodstype.tests.factories import GoodsTypeFactory
from letter_templates.models import LetterTemplate
from licences.enums import LicenceStatus
from licences.helpers import get_licence_reference_code
from licences.models import Licence
from organisations.enums import OrganisationType
from organisations.models import Organisation, ExternalLocation
from organisations.tests.factories import OrganisationFactory, SiteFactory
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
from static.countries.models import Country
from static.decisions.models import Decision
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
from users.enums import UserStatuses, SystemUser
from users.libraries.user_to_token import user_to_token
from users.models import ExporterUser, UserOrganisationRelationship, BaseUser, GovUser, Role
from workflow.flagging_rules_automation import apply_flagging_rules_to_case
from workflow.routing_rules.enum import RoutingRulesAdditionalFields
from workflow.routing_rules.models import RoutingRule


class Static:
    seeded = False


class DataTestClient(APITestCase, URLPatternsTestCase):
    """
    Test client which creates seeds the database with system data and sets up an initial organisation and user
    """

    urlpatterns = urlpatterns + static_urlpatterns
    client = APIClient
    faker = Faker()

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
        self.system_user = BaseUser.objects.get(id=SystemUser.id)

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
            "HTTP_ORGANISATION_ID": str(self.organisation.id),
        }

        self.default_role = Role.objects.get(id=Roles.INTERNAL_DEFAULT_ROLE_ID)
        self.super_user_role = Role.objects.get(id=Roles.INTERNAL_SUPER_USER_ROLE_ID)
        self.exporter_default_role = Role.objects.get(id=Roles.EXPORTER_DEFAULT_ROLE_ID)
        self.exporter_super_user_role = Role.objects.get(id=Roles.EXPORTER_SUPER_USER_ROLE_ID)

        self.hmrc_exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(self.hmrc_exporter_user),
            "HTTP_ORGANISATION_ID": str(self.hmrc_organisation.id),
        }

        self.queue = self.create_queue("Initial Queue", self.team)

        # Create a hardcoded list of control list entries rather than loading in the
        # spreadsheet each time
        ControlListEntry.objects.bulk_create(
            [
                ControlListEntry(rating=clc, text="Description", parent=None)
                for clc in [
                    "ML6b2",
                    "ML2a",
                    "ML7f1",
                    "5E002a",
                    "PL9011c",
                    "ML13c",
                    "1A004b",
                    "ML1d",
                    "PL9011a",
                    "5D002a1",
                    "ML6b1",
                    "ML13d1",
                    "1A005b",
                    "5A002e",
                    "5D002b",
                    "5A002a2",
                    "5A002c",
                    "ML13d2",
                    "5A002b",
                    "5A002a3",
                    "PL9011b",
                    "1A004a",
                    "ML1b2",
                    "5A002a1",
                    "ML1a",
                    "5A002a4",
                    "5A002d",
                    "1A005a",
                    "5E002b",
                    "ML3a",
                    "5D002c1",
                ]
            ]
        )
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

    def create_exporter_user(self, organisation=None, first_name=None, last_name=None, role=None):
        if not first_name and not last_name:
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()

        exporter_user = ExporterUser(first_name=first_name, last_name=last_name, email=self.faker.email(),)
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
        relation = UserOrganisationRelationship(user=exporter_user, organisation=organisation, role=role).save()
        return relation

    @staticmethod
    def create_external_location(name, org, country="GB"):
        external_location = ExternalLocation(
            name=name, address="20 Questions Road, Enigma", country=get_country(country), organisation=org,
        )
        external_location.save()
        return external_location

    @staticmethod
    def create_party(
        name, organisation, party_type, application=None, pk=None, country_code="GB", role=PartyRole.AGENT
    ):
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
            "country": get_country(country_code),
        }

        if party_type == PartyType.THIRD_PARTY:
            data["role"] = role

        party = Party(**data)
        party.save()

        if application and party_type == PartyType.ADDITIONAL_CONTACT:
            application.additional_contacts.add(party)
        elif application:
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
    def submit_application(application: BaseApplication, user: ExporterUser = None):
        if not user:
            user = UserOrganisationRelationship.objects.filter(organisation_id=application.organisation_id).first().user

        application.submitted_at = datetime.now(timezone.utc)
        application.sla_remaining_days = get_application_target_sla(application.case_type.sub_type)
        application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        application.save()

        if application.case_type.sub_type in [CaseTypeSubTypeEnum.STANDARD, CaseTypeSubTypeEnum.OPEN]:
            set_case_flags_on_submitted_standard_or_open_application(application)

        add_goods_flags_to_submitted_application(application)
        apply_flagging_rules_to_case(application)

        audit_trail_service.create(
            actor=user,
            verb=AuditType.UPDATED_STATUS,
            target=application.get_case(),
            payload={
                "status": {
                    "new": CaseStatusEnum.get_text(CaseStatusEnum.SUBMITTED),
                    "old": CaseStatusEnum.get_text(CaseStatusEnum.DRAFT),
                }
            },
        )

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
        warnings.warn(
            "create_flag is a deprecated function. Use a FlagFactory instead", category=DeprecationWarning, stacklevel=2
        )
        return FlagFactory(name=name, level=level, team=team)

    @staticmethod
    def create_flagging_rule(
        level: str,
        team: Team,
        flag: Flag,
        matching_value: str,
        status: str = FlagStatuses.ACTIVE,
        is_for_verified_goods_only=None,
    ):
        flagging_rule = FlaggingRule(
            level=level,
            team=team,
            flag=flag,
            matching_value=matching_value,
            status=status,
            is_for_verified_goods_only=is_for_verified_goods_only,
        )
        flagging_rule.save()
        return flagging_rule

    @staticmethod
    def create_case_assignment(queue, case, users):
        if isinstance(users, list):
            case_assignments = []
            for user in users:
                case_assignments.append(CaseAssignment.objects.create(queue=queue, case=case, user=user))
            return case_assignments
        else:
            return CaseAssignment.objects.create(queue=queue, case=case, user=users)

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
        organisation: Organisation,
        is_good_controlled: str = GoodControlled.NO,
        control_list_entries: Optional[List[str]] = None,
        is_pv_graded: str = GoodPvGraded.YES,
        pv_grading_details: PvGradingDetails = None,
        item_category=ItemCategory.GROUP1_DEVICE,
        is_military_use=MilitaryUse.NO,
        modified_military_use_details=None,
        component_details=None,
        is_component=None,
        uses_information_security=True,
        information_security_details=None,
        software_or_technology_details=None,
        create_firearm_details=False,
    ) -> Good:
        warnings.warn(
            "create_good is a deprecated function. Use a GoodFactory instead", category=DeprecationWarning, stacklevel=2
        )

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

        firearm_details = None
        if create_firearm_details:
            firearm_details = FirearmGoodDetails.objects.create(
                type=FirearmGoodType.AMMUNITION,
                calibre="0.5",
                year_of_manufacture="1991",
                is_covered_by_firearm_act_section_one_two_or_five=False,
                section_certificate_number=None,
                section_certificate_date_of_expiry=None,
                has_identification_markings=True,
                identification_markings_details="some marking details",
                no_identification_markings_details="",
            )

        good = Good(
            description=description,
            is_good_controlled=is_good_controlled,
            part_number="123456",
            organisation=organisation,
            comment=None,
            report_summary=None,
            is_pv_graded=is_pv_graded,
            pv_grading_details=pv_grading_details,
            item_category=item_category,
            is_military_use=is_military_use,
            is_component=is_component,
            uses_information_security=uses_information_security,
            information_security_details=information_security_details,
            modified_military_use_details=modified_military_use_details,
            component_details=component_details,
            software_or_technology_details=software_or_technology_details,
            firearm_details=firearm_details,
        )
        good.save()

        if good.is_good_controlled == GoodControlled.YES:
            if not control_list_entries:
                raise Exception("You need to set control list entries if the good is controlled")

            control_list_entries = ControlListEntry.objects.filter(rating__in=control_list_entries)
            good.control_list_entries.set(control_list_entries)

        return good

    def create_goods_query(self, description, organisation, clc_reason, pv_reason) -> GoodsQuery:
        good = DataTestClient.create_good(
            description=description, organisation=organisation, is_pv_graded=GoodPvGraded.NO
        )

        goods_query = GoodsQuery.objects.create(
            clc_raised_reasons=clc_reason,
            pv_grading_raised_reasons=pv_reason,
            good=good,
            organisation=organisation,
            case_type_id=CaseTypeEnum.GOODS.id,
            status=get_case_status_by_status(CaseStatusEnum.SUBMITTED),
            submitted_at=django.utils.timezone.now(),
            submitted_by=self.exporter_user,
        )
        goods_query.flags.add(Flag.objects.get(id=SystemFlags.GOOD_CLC_QUERY_ID))
        goods_query.flags.add(Flag.objects.get(id=SystemFlags.GOOD_PV_GRADING_QUERY_ID))
        goods_query.save()
        return goods_query

    def create_clc_query(self, description, organisation) -> GoodsQuery:
        good = DataTestClient.create_good(
            description=description, organisation=organisation, is_pv_graded=GoodPvGraded.NO
        )

        clc_query = GoodsQuery.objects.create(
            clc_raised_reasons="this is a test text",
            good=good,
            organisation=organisation,
            case_type_id=CaseTypeEnum.GOODS.id,
            status=get_case_status_by_status(CaseStatusEnum.SUBMITTED),
            submitted_at=django.utils.timezone.now(),
            submitted_by=self.exporter_user,
        )
        clc_query.flags.add(Flag.objects.get(id=SystemFlags.GOOD_CLC_QUERY_ID))
        clc_query.save()
        return clc_query

    @staticmethod
    def create_pv_grading_query(description, organisation) -> GoodsQuery:
        good = DataTestClient.create_good(
            description=description, organisation=organisation, is_pv_graded=GoodPvGraded.GRADING_REQUIRED
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
    def create_advice(
        user,
        case,
        advice_field,
        advice_type,
        level,
        pv_grading=None,
        advice_text="This is some text",
        good=None,
        goods_type=None,
    ):
        advice = Advice(
            user=user,
            case=case,
            type=advice_type,
            level=level,
            note="This is a note to the exporter",
            text=advice_text,
            pv_grading=pv_grading,
        )

        advice.team = user.team
        advice.save()

        if advice_field == "end_user":
            advice.end_user = StandardApplication.objects.get(pk=case.id).end_user.party

        if good:
            advice.good = good
        elif goods_type:
            advice.goods_type = goods_type
        elif advice_field == "good":
            if case.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
                advice.good = GoodOnApplication.objects.filter(application=case).first().good
            elif case.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
                advice.goods_type = GoodsType.objects.filter(application=case).first()

        if advice_type == AdviceType.PROVISO:
            advice.proviso = "I am easy to proviso"

        if advice_type == AdviceType.REFUSE:
            advice.denial_reasons.set(["1a", "1b", "1c"])

        advice.save()
        return advice

    @staticmethod
    def create_good_on_application(application, good):
        return GoodOnApplication.objects.create(
            good=good, application=application, quantity=10, unit=Units.NAR, value=500,
        )

    @staticmethod
    def add_additional_information(application):
        additional_information = {
            "expedited": False,
            "mtcr_type": "mtcr_category_2",
            "foreign_technology": False,
            "locally_manufactured": False,
            "uk_service_equipment": False,
            "uk_service_equipment_type": "mod_funded",
            "electronic_warfare_requirement": False,
            "prospect_value": 100.0,
        }
        for key, item in additional_information.items():
            setattr(application, key, item)

        application.save()

    def create_organisation_with_exporter_user(
        self, name="Organisation", org_type=OrganisationType.COMMERCIAL, exporter_user=None
    ):
        organisation = OrganisationFactory(name=name, type=org_type)

        if not exporter_user:
            exporter_user = self.create_exporter_user(organisation)
        else:
            self.add_exporter_user_to_org(organisation, exporter_user)

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
        parties=True,
        site=True,
        case_type_id=CaseTypeEnum.SIEL.id,
        add_a_good=True,
        user: ExporterUser = None,
        good=None,
    ):
        if not user:
            user = UserOrganisationRelationship.objects.filter(organisation_id=organisation.id).first().user

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
            intended_end_use="this is our intended end use",
            is_shipped_waybill_or_lading=True,
            non_waybill_or_lading_route_details=None,
            status_id="00000000-0000-0000-0000-000000000000",
            submitted_by=user,
        )

        application.save()

        if add_a_good:
            # Add a good to the standard application
            self.good_on_application = GoodOnApplication.objects.create(
                good=good if good else GoodFactory(organisation=organisation, is_good_controlled=GoodControlled.YES),
                application=application,
                quantity=10,
                unit=Units.NAR,
                value=500,
            )

        if parties:
            self.create_party("End User", organisation, PartyType.END_USER, application)
            self.create_party("Consignee", organisation, PartyType.CONSIGNEE, application)
            self.create_party("Third party", organisation, PartyType.THIRD_PARTY, application)
            # Set the application party documents

            self.add_party_documents(application, safe_document)

        self.create_application_document(application)

        # Add a site to the application
        if site:
            SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_mod_clearance_application(
        self,
        organisation,
        case_type,
        reference_name="MOD Clearance Draft",
        safe_document=True,
        additional_information=True,
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
            submitted_by=self.exporter_user,
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
            if additional_information:
                self.add_additional_information(application)
            application.intended_end_use = "intended end use here"
            application.save()
        else:
            self.create_party("End User", organisation, PartyType.END_USER, application)
            self.create_party("Third party", organisation, PartyType.THIRD_PARTY, application)
            self.add_party_documents(application, safe_document, consignee=case_type == CaseTypeEnum.EXHIBITION)

        if case_type not in [CaseTypeEnum.F680, CaseTypeEnum.EXHIBITION, CaseTypeEnum.GIFTING]:
            self.create_party("Consignee", organisation, PartyType.CONSIGNEE, application)

        # Add a good to the standard application
        self.good_on_application = GoodOnApplication.objects.create(
            good=GoodFactory(organisation=organisation, is_good_controlled=GoodControlled.YES),
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

    def create_mod_clearance_application_case(self, organisation, case_type):
        draft = self.create_mod_clearance_application(organisation, case_type)

        return self.submit_application(draft, self.exporter_user)

    def create_incorporated_good_and_ultimate_end_user_on_application(self, organisation, application):
        good = Good.objects.create(
            is_good_controlled=True, organisation=self.organisation, description="a good", part_number="123456",
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

        GoodOnApplication(
            good=GoodFactory(is_good_controlled=GoodControlled.YES, organisation=self.organisation,),
            application=application,
            quantity=17,
            value=18,
            is_good_incorporated=True,
        ).save()

        self.ultimate_end_user = self.create_party(
            "Ultimate End User", organisation, PartyType.ULTIMATE_END_USER, application
        )
        self.create_document_for_party(application.ultimate_end_users.first().party, safe=safe_document)

        return application

    def create_draft_open_application(
        self, organisation: Organisation, reference_name="Open Draft", case_type_id=CaseTypeEnum.OIEL.id
    ):
        application = OpenApplication(
            name=reference_name,
            case_type_id=case_type_id,
            export_type=ApplicationExportType.PERMANENT,
            activity="Trade",
            usage="Trade",
            organisation=organisation,
            status=get_case_status_by_status(CaseStatusEnum.DRAFT),
            is_military_end_use_controls=False,
            is_informed_wmd=False,
            is_suspected_wmd=False,
            intended_end_use="intended end use is none of your business",
            is_shipped_waybill_or_lading=True,
            non_waybill_or_lading_route_details=None,
            status_id="00000000-0000-0000-0000-000000000000",
            submitted_by=self.exporter_user,
        )

        application.save()

        # Add a goods description
        GoodsTypeFactory(application=application, is_good_controlled=True)
        GoodsTypeFactory(application=application, is_good_controlled=True)

        # Add a country to the application - GB cannot be a destination on licences!
        CountryOnApplication(application=application, country=get_country("FR")).save()

        # Add a site to the application
        SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_open_application_case(self, organisation: Organisation, reference_name="Open Application Case"):
        """
        Creates a complete open application case
        """
        draft = self.create_draft_open_application(organisation, reference_name)

        return self.submit_application(draft, self.exporter_user)

    def create_hmrc_query(
        self, organisation: Organisation, reference_name="HMRC Query", safe_document=True, have_goods_departed=False,
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
            have_goods_departed=have_goods_departed,
            submitted_by=self.hmrc_exporter_user,
        )
        application.save()

        end_user = self.create_party("End User", organisation, PartyType.END_USER, application)
        consignee = self.create_party("Consignee", organisation, PartyType.CONSIGNEE, application)
        third_party = self.create_party("Third party", organisation, PartyType.THIRD_PARTY, application)

        self.assertEqual(end_user, application.end_user.party)
        self.assertEqual(consignee, application.consignee.party)
        self.assertEqual(third_party, application.third_parties.get().party)

        goods_type = GoodsTypeFactory(application=application)

        # Set the application party documents
        self.create_document_for_party(application.end_user.party, safe=safe_document)
        self.create_document_for_party(application.consignee.party, safe=safe_document)
        self.create_document_for_party(application.third_parties.first().party, safe=safe_document)

        self.create_document_for_goods_type(goods_type)

        # Add a site to the application
        SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_standard_application_case(
        self, organisation: Organisation, reference_name="Standard Application Case", parties=True, site=True, user=None
    ):
        """
        Creates a complete standard application case
        """
        draft = self.create_draft_standard_application(
            organisation, reference_name, parties=parties, site=site, user=user
        )

        return self.submit_application(draft, self.exporter_user)

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
            submitted_by=self.exporter_user,
            submitted_at=datetime.now(timezone.utc),
        )
        end_user_advisory_query.save()
        return end_user_advisory_query

    def create_end_user_advisory_case(self, note: str, reasoning: str, organisation: Organisation):
        return self.create_end_user_advisory(note, reasoning, organisation)

    def create_generated_case_document(
        self, case, template, visible_to_exporter=True, document_name="Generated Doc", advice_type=None, licence=None
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
            licence=licence,
        )
        return generated_case_doc

    def create_letter_template(
        self,
        case_types,
        name=None,
        decisions=None,
        visible_to_exporter=True,
        letter_paragraph=None,
        digital_signature=False,
    ):
        if not name:
            name = str(uuid.uuid4())[0:35]
        if not letter_paragraph:
            letter_paragraph = self.create_picklist_item(
                "#1", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
            )
        letter_layout = LetterLayout.objects.get(id=uuid.UUID(int=1))

        letter_template = LetterTemplate.objects.create(
            name=name,
            layout=letter_layout,
            visible_to_exporter=visible_to_exporter,
            include_digital_signature=digital_signature,
        )
        if decisions:
            letter_template.decisions.set(decisions)
        letter_template.case_types.set(case_types)
        letter_template.letter_paragraphs.add(letter_paragraph)
        letter_template.save()

        return letter_template

    def create_ecju_query(self, case, question="ECJU question", gov_user=None):
        ecju_query = EcjuQuery(case=case, question=question, raised_by_user=gov_user if gov_user else self.gov_user)
        ecju_query.save()
        return ecju_query

    @staticmethod
    def create_licence(
        application: Case,
        status: LicenceStatus,
        reference_code=None,
        decisions=None,
        hmrc_integration_sent_at=None,
        start_date=None,
    ):
        if not decisions:
            decisions = [Decision.objects.get(name=AdviceType.APPROVE)]
        if not reference_code:
            reference_code = get_licence_reference_code(application.reference_code)
        if not start_date:
            start_date = django.utils.timezone.now().date()

        licence = Licence.objects.create(
            case=application,
            reference_code=reference_code,
            start_date=start_date,
            duration=get_default_duration(application),
            status=status,
            hmrc_integration_sent_at=hmrc_integration_sent_at,
        )
        licence.decisions.set(decisions)
        return licence

    def create_routing_rule(self, team_id, queue_id, tier, status_id, additional_rules: list):
        user = self.gov_user.id if RoutingRulesAdditionalFields.USERS in additional_rules else None
        flags = (
            [self.create_flag("routing_flag", FlagLevels.CASE, self.team).id]
            if RoutingRulesAdditionalFields.FLAGS in additional_rules
            else None
        )
        case_types = (
            [CaseType.objects.first().id] if RoutingRulesAdditionalFields.CASE_TYPES in additional_rules else None
        )
        country = Country.objects.first().id if RoutingRulesAdditionalFields.COUNTRY in additional_rules else None

        rule = RoutingRule.objects.create(
            team_id=team_id,
            queue_id=queue_id,
            tier=tier,
            status_id=status_id,
            additional_rules=additional_rules,
            user_id=user,
            country_id=country,
        )

        if case_types:
            rule.case_types.add(*case_types)
        if flags:
            rule.flags.add(*flags)

        rule.save()
        return rule


@tag("performance")
class PerformanceTestClient(DataTestClient):
    def setUp(self):
        super().setUp()
        print("\n---------------")
        print(self._testMethodName)
        # we need to set debug to true otherwise we can't see the amount of queries
        conf_settings.DEBUG = True
        settings.SUPPRESS_TEST_OUTPUT = True

    def timeit(self, request, amount=1):
        time = timeit.timeit(request, number=amount)
        print(f"queries: {len(connection.queries)}")
        print(f"time to hit endpoint: {time}")

        return time

    def create_organisations_multiple_users(self, required_user, organisations: int = 1, users_per_org: int = 10):
        for i in range(organisations):
            organisation, _ = self.create_organisation_with_exporter_user(exporter_user=required_user)
            for j in range(users_per_org):
                self.create_exporter_user(organisation=organisation)

    def create_multiple_sites_for_an_organisation(self, organisation, sites_count: int = 10, users_per_site: int = 1):
        users = [UserOrganisationRelationship.objects.get(user=self.exporter_user)]
        organisation = self.organisation if not organisation else organisation

        for i in range(users_per_site):
            user = self.create_exporter_user(self.organisation)
            users.append(UserOrganisationRelationship.objects.get(user=user))

        for i in range(sites_count):
            site = SiteFactory(organisation=organisation)
            site.users.set(users)

    def create_assorted_cases(
        self,
        standard_app_case_count: int = 1,
        open_app_case_count: int = 1,
        hmrc_query_count_goods_gone: int = 1,
        hmrc_query_count_goods_in_uk: int = 1,
    ):
        print(f"Creating {standard_app_case_count} standard cases...")
        for i in range(standard_app_case_count):
            self.create_standard_application_case(self.organisation)

        print(f"Creating {open_app_case_count} open cases...")
        for i in range(open_app_case_count):
            self.create_open_application_case(self.organisation)

        print(f"Creating {hmrc_query_count_goods_gone} HMRC Queries where the products have left the UK...")
        for i in range(hmrc_query_count_goods_gone):
            self.create_hmrc_query(self.organisation, have_goods_departed=True)

        print(f"Creating {hmrc_query_count_goods_in_uk} HMRC Queries where the products are still in the UK...")
        for i in range(hmrc_query_count_goods_in_uk):
            self.create_hmrc_query(self.organisation, have_goods_departed=True)

    def create_batch_queues(self, queue_count):
        print(f"creating {queue_count} queues")
        queue_details = {"name": "random", "team": self.team}
        Queue.objects.bulk_create([Queue(**queue_details) for i in range(0, queue_count)])
