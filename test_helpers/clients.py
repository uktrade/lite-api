import random
import timeit
import uuid
import sys
from django.utils import timezone
from typing import Tuple

import django.utils.timezone
from django.db import connection
from django.test import override_settings
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient
import pytest

from api.applications.libraries.edit_applications import set_case_flags_on_submitted_standard_application
from api.applications.libraries.goods_on_applications import add_goods_flags_to_submitted_application
from api.applications.models import (
    BaseApplication,
    GoodOnApplication,
    SiteOnApplication,
    StandardApplication,
    ApplicationDocument,
)
from api.applications.tests.factories import (
    GoodOnApplicationFactory,
    PartyOnApplicationFactory,
    StandardApplicationFactory,
)
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.bookmarks.models import Bookmark
from api.cases.enums import AdviceType, CaseDocumentState, CaseTypeEnum, CaseTypeSubTypeEnum
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.models import (
    CaseNote,
    Case,
    CaseDocument,
    CaseAssignment,
    EcjuQuery,
    CaseType,
    Advice,
    CaseNoteMentions,
)
from api.cases.celery_tasks import get_application_target_sla
from django.conf import settings
from api.core.constants import GovPermissions, Roles
from api.conf.urls import urlpatterns
from api.documents.libraries.s3_operations import init_s3_client
from api.flags.enums import SystemFlags, FlagStatuses, FlagLevels
from api.flags.models import Flag, FlaggingRule
from api.flags.tests.factories import FlagFactory
from api.addresses.tests.factories import AddressFactoryGB
from api.goods.enums import GoodPvGraded
from api.goods.models import Good, GoodDocument
from api.applications.models import GoodOnApplicationInternalDocument
from api.goods.tests.factories import GoodFactory
from api.letter_templates.models import LetterTemplate
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import StandardLicenceFactory
from api.organisations.enums import OrganisationType
from api.organisations.models import Organisation, ExternalLocation
from api.organisations.tests.factories import OrganisationFactory, SiteFactory
from api.parties.enums import SubType, PartyType, PartyRole
from api.parties.models import Party
from api.parties.models import PartyDocument
from api.parties.tests.factories import ConsigneeFactory, EndUserFactory, ThirdPartyFactory, UltimateEndUserFactory
from api.picklists.enums import PickListStatus, PicklistType
from api.picklists.models import PicklistItem
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.queries.goods_query.models import GoodsQuery
from api.queues.models import Queue
from api.staticdata.countries.helpers import get_country
from api.staticdata.countries.models import Country
from api.staticdata.letter_layouts.models import LetterLayout
from api.staticdata.management.commands import seedall
from api.staticdata.management.commands.seedall import SEED_COMMANDS
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.units.enums import Units
from api.staticdata.urls import urlpatterns as static_urlpatterns
from api.teams.models import Team
from api.users.tests.factories import GovUserFactory
from test_helpers import colours
from test_helpers.faker import faker
from api.users.enums import SystemUser, UserType
from api.users.libraries.user_to_token import user_to_token
from api.users.models import ExporterUser, UserOrganisationRelationship, BaseUser, GovUser, Role
from lite_routing.routing_rules_internal.flagging_engine import apply_flagging_rules_to_case
from api.workflow.routing_rules.enum import RoutingRulesAdditionalFields
from api.workflow.routing_rules.models import RoutingRule


class Static:
    seeded = False


class DataTestClient(APITestCase, URLPatternsTestCase):
    """
    Test client which creates seeds the database with system data and sets up an initial organisation and user
    """

    urlpatterns = urlpatterns + static_urlpatterns
    client = APIClient
    faker = faker  # Assigning this to the class as `self.faker` is expected in tests

    INITIAL_QUEUE_ID = uuid.uuid4()

    @classmethod
    def setUpClass(cls):
        """Run seed operations ONCE for the entire test suite."""
        if not Static.seeded:
            # HACK: Don't seed if we already seeeded and use --reuse-db or similar
            if "--reuse-db" in sys.argv or "--keepdb" in sys.argv:
                from django.contrib.auth import get_user_model

                user_model = get_user_model()
                if user_model.objects.count():
                    Static.seeded = True
                    return

            seedall.Command.seed_list(SEED_COMMANDS["Tests"])
            Static.seeded = True

    @classmethod
    def tearDownClass(cls):
        """tearDownClass is required if `super()` isn't called within `setUpClass`"""
        pass

    def setUp(self):
        self.system_user = BaseUser.objects.get(id=SystemUser.id)

        # Gov User Setup
        self.team = Team.objects.get(name="Admin")
        self.base_user = BaseUser(email="test@mail.com", first_name="John", last_name="Smith", type=UserType.INTERNAL)
        self.base_user.save()
        self.gov_user = GovUser(baseuser_ptr=self.base_user, team=self.team)
        self.gov_user.save()
        self.gov_headers = {"HTTP_GOV_USER_TOKEN": user_to_token(self.base_user)}

        self.lu_case_officer = GovUserFactory(
            baseuser_ptr__email="case.officer@lu.gov.uk",
            baseuser_ptr__first_name="Case",
            baseuser_ptr__last_name="Officer",
            team=Team.objects.get(name="Licensing Unit"),
        )
        self.lu_case_officer_headers = {"HTTP_GOV_USER_TOKEN": user_to_token(self.lu_case_officer.baseuser_ptr)}
        self.lu_case_officer.role.permissions.set(
            [GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        # Exporter User Setup
        (self.organisation, self.exporter_user) = self.create_organisation_with_exporter_user()
        (self.hmrc_organisation, self.hmrc_exporter_user) = self.create_organisation_with_exporter_user(
            "HMRC org 5843", org_type=OrganisationType.HMRC
        )

        self.exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(self.exporter_user.baseuser_ptr),
            "HTTP_ORGANISATION_ID": str(self.organisation.id),
        }

        self.default_role = Role.objects.get(id=Roles.INTERNAL_DEFAULT_ROLE_ID)
        self.super_user_role = Role.objects.get(id=Roles.INTERNAL_SUPER_USER_ROLE_ID)
        self.exporter_default_role = Role.objects.get(id=Roles.EXPORTER_EXPORTER_ROLE_ID)
        self.exporter_super_user_role = Role.objects.get(id=Roles.EXPORTER_ADMINISTRATOR_ROLE_ID)

        self.hmrc_exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(self.hmrc_exporter_user.baseuser_ptr),
            "HTTP_ORGANISATION_ID": str(self.hmrc_organisation.id),
        }

        self.queue = self.create_queue("Initial Queue", self.team, pk=self.INITIAL_QUEUE_ID)

        if settings.TIME_TESTS:
            self.tick = timezone.localtime()

    def setup_exporter_headers(self, exporter_user):
        """
        Sets exporter_headers for given exporter user
        """
        self.exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(exporter_user.baseuser_ptr),
            "HTTP_ORGANISATION_ID": str(exporter_user.organisation.id),
        }

    def tearDown(self):
        """
        Print output time for tests if settings.TIME_TESTS is set to True
        """
        if settings.SUPPRESS_TEST_OUTPUT:
            pass
        elif settings.TIME_TESTS:
            self.tock = timezone.localtime()

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
        base_user = BaseUser(
            first_name=first_name,
            last_name=last_name,
            email=self.faker.unique.email(),
            pending=False,
            type=UserType.EXPORTER,
        )
        base_user.save()
        exporter_user = ExporterUser(baseuser_ptr=base_user)
        exporter_user.organisation = organisation
        exporter_user.save()

        if organisation:
            if not role:
                role = Role.objects.get(id=Roles.EXPORTER_EXPORTER_ROLE_ID)
            UserOrganisationRelationship(user=exporter_user, organisation=organisation, role=role).save()
            # exporter_user.status = UserStatuses.ACTIVE

        return exporter_user

    @staticmethod
    def add_exporter_user_to_org(organisation, exporter_user, role=None):
        if not role:
            role = Role.objects.get(id=Roles.EXPORTER_EXPORTER_ROLE_ID)
        relation = UserOrganisationRelationship(user=exporter_user, organisation=organisation, role=role).save()
        return relation

    @staticmethod
    def create_external_location(name, org, country="GB"):
        external_location = ExternalLocation(
            name=name, address="20 Questions Road, Enigma", country=get_country(country), organisation=org
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
    def create_case_note(case: Case, text: str, user: BaseUser, is_visible_to_exporter: bool = False):
        case_note = CaseNote(case=case, text=text, user=user, is_visible_to_exporter=is_visible_to_exporter)
        case_note.save()
        return case_note

    @staticmethod
    def create_case_note_mention(case_note: CaseNote, user: GovUser):
        case_note_mention = CaseNoteMentions(case_note=case_note, user=user)
        case_note_mention.save()
        return case_note_mention

    @staticmethod
    def create_queue(name: str, team: Team, pk=None):
        if not pk:
            pk = uuid.uuid4()
        queue = Queue(id=pk, name=name, team=team)
        queue.save()
        return queue

    @staticmethod
    def create_gov_user(email: str, team: Team) -> GovUser:
        gov_user = GovUserFactory(baseuser_ptr__email=email, team=team)
        gov_user.save()
        return gov_user

    @staticmethod
    def create_team(name: str) -> Team:
        team = Team(name=name)
        team.save()
        return team

    @staticmethod
    def submit_application(application: BaseApplication, user: ExporterUser = None):
        if not user:
            user = UserOrganisationRelationship.objects.filter(organisation_id=application.organisation_id).first().user

        application.submitted_at = timezone.localtime()
        application.sla_remaining_days = get_application_target_sla(application.case_type.sub_type)
        application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        application.save()

        if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
            set_case_flags_on_submitted_standard_application(application)

        add_goods_flags_to_submitted_application(application)
        apply_flagging_rules_to_case(application)

        audit_trail_service.create(
            actor=user.baseuser_ptr,
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
    def create_case_document(case: Case, user: GovUser, name: str, visible_to_exporter=True, safe=True):
        case_doc = CaseDocument(
            case=case,
            description="This is a document",
            user=user,
            name=name,
            s3_key="thisisakey",
            size=123456,
            virus_scanned_at=None,
            safe=safe,
            visible_to_exporter=visible_to_exporter,
        )
        case_doc.save()
        return case_doc

    @staticmethod
    def create_application_document(application, safe=True) -> ApplicationDocument:
        application_doc = ApplicationDocument(
            application=application,
            description="document description",
            name="document name",
            s3_key="documentkey",
            size=12,
            virus_scanned_at=django.utils.timezone.now(),
            safe=safe,
        )

        application_doc.save()
        return application_doc

    @staticmethod
    def create_good_document(
        good: Good, user: ExporterUser, organisation: Organisation, name: str, s3_key: str, safe=True
    ):
        good_doc = GoodDocument(
            good=good,
            description="This is a document",
            user=user,
            organisation=organisation,
            name=name,
            s3_key=s3_key,
            size=123456,
            virus_scanned_at=django.utils.timezone.now(),
            safe=safe,
        )
        good_doc.save()
        return good_doc

    @staticmethod
    def create_good_on_application_internal_document(
        good_on_application: GoodOnApplication, name: str, document_title: str, s3_key: str, safe=True
    ):
        good_internal_doc = GoodOnApplicationInternalDocument(
            good_on_application=good_on_application,
            document_title=document_title,
            name=name,
            s3_key=s3_key,
            size=123456,
            virus_scanned_at=django.utils.timezone.now(),
            safe=safe,
        )
        good_internal_doc.save()
        return good_internal_doc

    @staticmethod
    def create_document_for_party(party: Party, name="document_name.pdf", safe=True):
        document = PartyDocument(
            party=party, name=name, s3_key="s3_keykey.pdf", size=123456, virus_scanned_at=None, safe=safe
        )
        document.save()
        return document

    @staticmethod
    def create_flag(name: str, level: str, team: Team):
        return FlagFactory(name=name, level=level, team=team)

    @staticmethod
    def create_flagging_rule(
        level: str,
        team: Team,
        flag: Flag,
        matching_values: list,
        matching_groups: list = None,
        excluded_values: list = None,
        status: str = FlagStatuses.ACTIVE,
        is_for_verified_goods_only=None,
    ):
        flagging_rule = FlaggingRule(
            level=level,
            team=team,
            flag=flag,
            matching_values=matching_values,
            matching_groups=matching_groups if matching_groups else [],
            excluded_values=excluded_values if excluded_values else [],
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

    def create_goods_query(self, description, organisation, clc_reason, pv_reason) -> GoodsQuery:
        good = GoodFactory(name=description, organisation=organisation)

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
        good = GoodFactory(name=description, organisation=organisation)

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
        good = GoodFactory(name=description, organisation=organisation, is_pv_graded=GoodPvGraded.GRADING_REQUIRED)

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
        countersign_comments="",
        countersigned_by=None,
    ):
        advice = Advice(
            user=user,
            case=case,
            type=advice_type,
            level=level,
            note="This is a note to the exporter",
            proviso="",
            text=advice_text,
            pv_grading=pv_grading,
            countersign_comments=countersign_comments,
            countersigned_by=countersigned_by,
        )

        advice.team = user.team
        advice.save()

        if advice_field == "consignee":
            advice.end_user = StandardApplication.objects.get(pk=case.id).end_user.party
        if advice_field == "end_user":
            advice.end_user = StandardApplication.objects.get(pk=case.id).end_user.party
        if advice_field == "third_party":
            advice.end_user = StandardApplication.objects.get(pk=case.id).end_user.party

        if good:
            advice.good = good
        elif advice_field == "good":
            if case.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
                advice.good = GoodOnApplication.objects.filter(application=case).first().good

        if advice_type == AdviceType.PROVISO:
            advice.proviso = "I am easy to proviso"

        if advice_type == AdviceType.REFUSE:
            advice.denial_reasons.set(["1a", "1b", "1c"])

        advice.save()
        return advice

    @staticmethod
    def create_good_on_application(application, good):
        return GoodOnApplication.objects.create(
            good=good, application=application, quantity=10, unit=Units.NAR, value=500
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
    ) -> Tuple[Organisation, ExporterUser]:
        site_gb = SiteFactory(address=AddressFactoryGB())
        organisation = OrganisationFactory(name=name, type=org_type, primary_site=site_gb)

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
        ultimate_end_users=False,
        site=True,
        case_type_id=CaseTypeEnum.SIEL.id,
        add_a_good=True,
        user: ExporterUser = None,
        good=None,
        num_products=1,
        reuse_good=False,
    ):
        if not user:
            user = UserOrganisationRelationship.objects.filter(organisation_id=organisation.id).first().user

        application = StandardApplicationFactory(
            name=reference_name,
            case_type_id=case_type_id,
            organisation=organisation,
            status=get_case_status_by_status(CaseStatusEnum.DRAFT),
            submitted_by=user,
        )

        if add_a_good:
            if reuse_good:
                good = GoodFactory(organisation=organisation, is_good_controlled=True)

            for _ in range(num_products):
                GoodOnApplicationFactory(
                    good=good if reuse_good else GoodFactory(organisation=organisation, is_good_controlled=True),
                    application=application,
                    quantity=random.randint(1, 50),
                    unit=Units.NAR,
                    value=random.randint(100, 5000),
                )

        if parties:
            PartyOnApplicationFactory(application=application, party=ConsigneeFactory(organisation=self.organisation))
            PartyOnApplicationFactory(application=application, party=EndUserFactory(organisation=self.organisation))
            PartyOnApplicationFactory(application=application, party=ThirdPartyFactory(organisation=self.organisation))

            if ultimate_end_users:
                PartyOnApplicationFactory(application=application, party=UltimateEndUserFactory())

            self.add_party_documents(application, safe_document)

        self.create_application_document(application)

        # Add a site to the application
        if site:
            SiteOnApplication(site=organisation.primary_site, application=application).save()

        return application

    def create_incorporated_good_and_ultimate_end_user_on_application(self, organisation, application):
        good = Good.objects.create(
            is_good_controlled=True, organisation=self.organisation, description="a good", part_number="123456"
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
        self,
        organisation: Organisation,
        reference_name="Standard Draft",
        safe_document=True,
        destination_country_code="GB",
        good_cles=None,
        good_kwargs=None,
        is_good_incorporated=True,
        is_onward_incorporated=False,
    ):
        application = self.create_draft_standard_application(
            organisation, reference_name, safe_document, num_products=0, ultimate_end_users=True
        )
        if not good_kwargs:
            good_kwargs = {}

        good = GoodFactory(is_good_controlled=True, organisation=self.organisation, **good_kwargs)
        if good_cles != None:
            good.control_list_entries.clear()
            for cle in good_cles:
                good.control_list_entries.add(cle)

        GoodOnApplication(
            good=good,
            application=application,
            quantity=17,
            value=18,
            is_good_incorporated=is_good_incorporated,
            is_onward_incorporated=is_onward_incorporated,
        ).save()

        self.create_document_for_party(application.ultimate_end_users.first().party, safe=safe_document)

        return application

    def create_standard_application_case(
        self,
        organisation: Organisation,
        reference_name="Standard Application Case",
        parties=True,
        ultimate_end_users=False,
        site=True,
        user=None,
        num_products=1,
        reuse_good=False,
        add_a_good=True,
    ):
        """
        Creates a complete standard application case
        """
        draft = self.create_draft_standard_application(
            organisation,
            reference_name,
            parties=parties,
            ultimate_end_users=ultimate_end_users,
            site=site,
            user=user,
            num_products=num_products,
            reuse_good=reuse_good,
            add_a_good=add_a_good,
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
            submitted_at=timezone.localtime(),
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
            virus_scanned_at=timezone.localtime(),
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

        letter_template, _ = LetterTemplate.objects.get_or_create(
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

    def create_ecju_query(self, case, question="ECJU question", gov_user=None, created_at=None, responded_at=None):
        ecju_query = EcjuQuery(case=case, question=question, raised_by_user=gov_user if gov_user else self.gov_user)
        if created_at:
            ecju_query.created_at = created_at
        if responded_at:
            ecju_query.responded_at = responded_at
        ecju_query.save()
        return ecju_query

    @staticmethod
    def create_licence(
        application: Case,
        status: LicenceStatus,
    ):
        return StandardLicenceFactory(
            case=application,
            status=status,
        )

    def create_routing_rule(
        self, team_id, queue_id, tier, status_id, additional_rules: list, is_python_criteria=False, active=True
    ):
        user = self.gov_user.pk if RoutingRulesAdditionalFields.USERS in additional_rules else None
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
            is_python_criteria=is_python_criteria,
            active=active,
        )

        if case_types:
            rule.case_types.add(*case_types)
        if flags:
            rule.flags_to_include.add(*flags)

        rule.save()
        return rule

    def create_audit(
        self,
        actor,
        verb,
        action_object=None,
        target=None,
        payload=None,
        ignore_case_status=False,
    ):
        if not payload:
            payload = {}

        return Audit.objects.create(
            actor=actor,
            verb=verb.value,
            action_object=action_object,
            target=target,
            payload=payload,
            ignore_case_status=ignore_case_status,
        )

    def add_users(self, count=3):
        out = []
        for i in range(count):
            user = GovUserFactory(
                baseuser_ptr__email=f"test{i}@mail.com",
                baseuser_ptr__first_name=f"John{i}",
                baseuser_ptr__last_name=f"Smith{i}",
                team=self.team,
                role=self.default_role,
            )
            out.append(user)
        return out

    def create_default_bucket(self):
        s3 = init_s3_client()
        s3.create_bucket(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CreateBucketConfiguration={
                "LocationConstraint": settings.AWS_REGION,
            },
        )

    def put_object_in_default_bucket(self, key, body):
        s3 = init_s3_client()
        s3.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            Body=body,
        )

    def get_object_from_default_bucket(self, key):
        s3 = init_s3_client()
        return s3.get_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
        )

    def set_application_status(self, application, status_name):
        application.status = get_case_status_by_status(status_name)
        application.save()


@pytest.mark.performance
# we need to set debug to true otherwise we can't see the amount of queries
@override_settings(DEBUG=True, SUPPRESS_TEST_OUTPUT=True)
class PerformanceTestClient(DataTestClient):
    def setUp(self):
        super().setUp()
        print("\n---------------")
        print(self._testMethodName)

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
        print(f"Creating {standard_app_case_count} standard api.cases...")
        for i in range(standard_app_case_count):
            self.create_standard_application_case(self.organisation)

        print(f"Creating {open_app_case_count} open api.cases...")
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

    @staticmethod
    def add_bookmark(user_id, name, description, filter_json):
        Bookmark(id=uuid.uuid4(), user=user_id, name=name, description=description, filter_json=filter_json)
