import os
from datetime import datetime
from pathlib import Path
import subprocess

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase

from api.appeals.tests.factories import AppealFactory
from api.appeals.models import Appeal
from api.applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from api.applications.models import GoodOnApplication, StandardApplication
from api.audit_trail.tests.factories import AuditFactory
from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.cases.tests.factories import CaseNoteFactory, EcjuQueryFactory, FinalAdviceFactory
from api.cases.models import CaseNote, EcjuQuery, Advice
from api.documents.tests.factories import DocumentFactory
from api.documents.models import Document
from api.document_data.models import DocumentData
from api.goods.tests.factories import FirearmFactory, GoodFactory
from api.goods.models import FirearmGoodDetails, Good
from api.organisations.tests.factories import SiteFactory, OrganisationFactory
from api.organisations.models import Site, Organisation
from api.addresses.tests.factories import AddressFactory
from api.addresses.models import Address
from api.staticdata.countries.models import Country
from api.queries.end_user_advisories.tests.factories import EndUserAdvisoryQueryFactory
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.external_data.tests.factories import DenialFactory
from api.external_data.models import Denial
from api.parties.tests.factories import PartyFactory
from api.parties.models import Party
from api.users.tests.factories import BaseUserFactory, RoleFactory, GovUserFactory
from api.users.models import BaseUser, GovUser


# Note: This must inherit from TransactionTestCase - if we use DataTestClient
# instead, the DB state changes will occur in transactions that are not
# visible to the pg_dump command called by db_anonymiser
class TestAnonymiseDumps(TransactionTestCase):
    def _fixture_teardown(self):
        # NOTE: TransactionTestCase will truncate all tables by default
        # before the run of each test case.  By overriding this method,
        # we prevent this truncation from happening.  It would be nice if Django
        # supplied some configurable way to do this, but that does not seem to be
        # the case.
        return

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.create_test_data()
        cls.dump_location = f"/tmp/{settings.DB_ANONYMISER_DUMP_FILE_NAME}"
        try:
            os.remove(cls.dump_location)
        except FileNotFoundError:
            pass

        call_command("dump_and_anonymise", keep_local_dumpfile=True, skip_s3_upload=True)
        with open(cls.dump_location, "r") as f:
            cls.anonymised_sql = f.read()

        # Drop the existing test DB
        connection.close()
        db_details = settings.DATABASES["default"]
        postgres_url_base = (
            f"postgresql://{db_details['USER']}:{db_details['PASSWORD']}@{db_details['HOST']}:{db_details['PORT']}"
        )
        postgres_db_url = f"{postgres_url_base}/postgres"
        subprocess.run(
            (
                "psql",
                "--dbname",
                postgres_db_url,
            ),
            input=f"DROP DATABASE \"{db_details['NAME']}\"; CREATE DATABASE \"{db_details['NAME']}\";",
            encoding="utf-8",
            stdout=subprocess.PIPE,
        )

        # Load the dumped data in to the test DB
        lite_db_url = f"{postgres_url_base}/{db_details['NAME']}"
        subprocess.run(
            (
                "psql",
                "--dbname",
                lite_db_url,
            ),
            input=cls.anonymised_sql,
            encoding="utf-8",
            stdout=subprocess.PIPE,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.delete_test_data()

    @classmethod
    def create_test_data(cls):
        # Required as GovUser creation assumes this role exists
        RoleFactory(id="00000000-0000-0000-0000-000000000001")
        cls.document_data = DocumentData.objects.create(
            s3_key="somefile.txt", content_type="csv", last_modified=datetime.now()
        )
        cls.site = SiteFactory(name="some site")
        cls.organisation = OrganisationFactory(
            name="some org",
            phone_number="+4466019250102",
            website="someexample.net",
            eori_number="some_eori",
            sic_number="some_sic",
            vat_number="some_vat",
            registration_number="some_reg",
        )
        cls.address = AddressFactory(
            address_line_1="my address line 1",
            address_line_2="my address line 2",
            region="my region",
            postcode="my postc",
            city="my city",
            country__name="France",
        )
        cls.end_user_advisory_query = EndUserAdvisoryQueryFactory(
            contact_name="EUA name", contact_telephone="+4499919250102", contact_email="email@example.net"
        )
        cls.denial = DenialFactory(
            name="denial name",
            address="denial address",
            consignee_name="denial consignee name",
        )
        cls.party = PartyFactory(
            name="party name",
            address="party address",
            website="party.website",
            email="party@email.net",
            phone_number="+44party_no",
            signatory_name_euu="party signatory",
            details="party details",
        )
        cls.base_user = BaseUserFactory(
            first_name="base user first",
            last_name="base user last",
            email="base@user.email",
            phone_number="+44baseuser",
        )
        cls.appeal = AppealFactory(grounds_for_appeal="appeal grounds")
        cls.case_note = CaseNoteFactory(text="case note text")
        cls.advice = FinalAdviceFactory(
            text="final advice text", user=GovUserFactory(), note="advice note", proviso="advice proviso"
        )
        cls.ecju_query = EcjuQueryFactory(question="ecju query question", response="ecju query response")
        cls.document = DocumentFactory(name="document_name.txt", s3_key="document_s3_key.txt")
        cls.firearm_good_details = FirearmFactory(
            serial_numbers=["serial number 1", "serial number 2"], serial_number="serial number"
        )
        cls.good = GoodFactory(description="some good description", organisation=OrganisationFactory())
        cls.good_on_application = GoodOnApplicationFactory(
            comment="some goa comment", application=StandardApplicationFactory(), good=cls.good
        )
        cls.create_audit_trail_data()

    @classmethod
    def create_audit_trail_data(cls):
        cls.audit_entries = {
            AuditType.ADD_CASE_OFFICER_TO_CASE: AuditFactory(
                verb=AuditType.ADD_CASE_OFFICER_TO_CASE, payload={"case_officer": "some officer"}
            ),
            AuditType.ADD_PARTY: AuditFactory(
                verb=AuditType.ADD_PARTY, payload={"party_name": "some party", "party_type": "ultimate_end_user"}
            ),
            AuditType.APPROVED_ORGANISATION: AuditFactory(
                verb=AuditType.APPROVED_ORGANISATION, payload={"organisation_name": "some organisation"}
            ),
            AuditType.ASSIGN_USER_TO_CASE: AuditFactory(
                verb=AuditType.ASSIGN_USER_TO_CASE,
                payload={"additional_text": "allocated self to the case", "queue": "some queue", "user": "some user"},
            ),
            AuditType.CREATE_REFUSAL_CRITERIA: AuditFactory(
                verb=AuditType.CREATE_REFUSAL_CRITERIA,
                payload={
                    "additional_text": "some text",
                    "advice_type": "refuse",
                    "firstname": "somefirst",
                    "lastname": "somelast",
                },
            ),
            AuditType.CREATED_CASE_NOTE: AuditFactory(
                verb=AuditType.CREATED_CASE_NOTE,
                payload={
                    "additional_text": "some text",
                },
            ),
            AuditType.CREATED_CASE_NOTE_WITH_MENTIONS: AuditFactory(
                verb=AuditType.CREATED_CASE_NOTE_WITH_MENTIONS,
                payload={
                    "additional_text": "some text",
                    "mention_users": ["user one", "user two"],
                },
            ),
            AuditType.CREATED_ORGANISATION: AuditFactory(
                verb=AuditType.CREATED_ORGANISATION,
                payload={
                    "organisation_name": "some organisation",
                },
            ),
            AuditType.CREATED_SITE: AuditFactory(
                verb=AuditType.CREATED_SITE,
                payload={
                    "site_name": "some site",
                },
            ),
            AuditType.DELETE_APPLICATION_DOCUMENT: AuditFactory(
                verb=AuditType.DELETE_APPLICATION_DOCUMENT,
                payload={
                    "file_name": "somefile.txt",
                },
            ),
            AuditType.DELETE_PARTY_DOCUMENT: AuditFactory(
                verb=AuditType.DELETE_PARTY_DOCUMENT,
                payload={
                    "file_name": "somefile.txt",
                    "party_name": "some party",
                    "party_type": "end_user",
                },
            ),
            AuditType.DESTINATION_ADD_FLAGS: AuditFactory(
                verb=AuditType.DESTINATION_ADD_FLAGS,
                payload={
                    "added_flags": ["flag1", "flag2"],
                    "destination_name": "some destination",
                },
            ),
            AuditType.DOCUMENT_ON_ORGANISATION_CREATE: AuditFactory(
                verb=AuditType.DOCUMENT_ON_ORGANISATION_CREATE,
                payload={
                    "file_name": "somefile.txt",
                    "document_type": "some doc type",
                },
            ),
            AuditType.DOCUMENT_ON_ORGANISATION_DELETE: AuditFactory(
                verb=AuditType.DOCUMENT_ON_ORGANISATION_DELETE,
                payload={
                    "file_name": "somefile.txt",
                    "document_type": "some doc type",
                },
            ),
            AuditType.ECJU_QUERY: AuditFactory(
                verb=AuditType.ECJU_QUERY,
                payload={
                    "ecju_query": "some query",
                },
            ),
            AuditType.ECJU_QUERY_MANUALLY_CLOSED: AuditFactory(
                verb=AuditType.ECJU_QUERY_MANUALLY_CLOSED,
                payload={
                    "ecju_response": "some response",
                },
            ),
            AuditType.ECJU_QUERY_RESPONSE: AuditFactory(
                verb=AuditType.ECJU_QUERY_RESPONSE,
                payload={
                    "ecju_response": "some response",
                },
            ),
            AuditType.LU_ADVICE: AuditFactory(
                verb=AuditType.LU_ADVICE,
                payload={
                    "advice_type": "proviso",
                    "firstname": "somefirst",
                    "lastname": "somelast",
                },
            ),
            AuditType.LU_COUNTERSIGN: AuditFactory(
                verb=AuditType.LU_COUNTERSIGN,
                payload={
                    "firstname": "somefirst",
                    "lastname": "somelast",
                    "department": "somedept",
                    "countersign_accepted": True,
                    "order": 1,
                },
            ),
            AuditType.LU_CREATE_MEETING_NOTE: AuditFactory(
                verb=AuditType.LU_CREATE_MEETING_NOTE,
                payload={
                    "firstname": "somefirst",
                    "lastname": "somelast",
                    "advice_type": "proviso",
                    "additional_text": "some text",
                },
            ),
            AuditType.LU_EDIT_ADVICE: AuditFactory(
                verb=AuditType.LU_EDIT_ADVICE,
                payload={
                    "firstname": "somefirst",
                    "lastname": "somelast",
                    "advice_type": "proviso",
                    "additional_text": "some text",
                },
            ),
            AuditType.LU_EDIT_MEETING_NOTE: AuditFactory(
                verb=AuditType.LU_EDIT_MEETING_NOTE,
                payload={
                    "firstname": "somefirst",
                    "lastname": "somelast",
                    "advice_type": "proviso",
                    "additional_text": "some text",
                },
            ),
            AuditType.REGISTER_ORGANISATION: AuditFactory(
                verb=AuditType.REGISTER_ORGANISATION,
                payload={
                    "organisation_name": "some organisation",
                    "email": "email@example.net",
                },
            ),
            AuditType.REJECTED_ORGANISATION: AuditFactory(
                verb=AuditType.REJECTED_ORGANISATION,
                payload={
                    "organisation_name": "some organisation",
                },
            ),
            AuditType.REMOVE_CASE_OFFICER_FROM_CASE: AuditFactory(
                verb=AuditType.REMOVE_CASE_OFFICER_FROM_CASE,
                payload={
                    "case_officer": "some officer",
                },
            ),
            AuditType.REMOVE_PARTY: AuditFactory(
                verb=AuditType.REMOVE_PARTY,
                payload={
                    "party_name": "some party",
                    "party_type": "end_user",
                },
            ),
            AuditType.REMOVE_USER_FROM_CASE: AuditFactory(
                verb=AuditType.REMOVE_USER_FROM_CASE,
                payload={
                    "removed_user_id": "some id",
                    "removed_user_name": "some name",
                    "removed_user_queue_id": "some id",
                    "removed_user_queue_name": "some queue",
                },
            ),
            AuditType.UPDATE_APPLICATION_END_USE_DETAIL: AuditFactory(
                verb=AuditType.UPDATE_APPLICATION_END_USE_DETAIL,
                payload={
                    "end_use_detail": "some detail",
                    "new_end_use_detail": "some detail",
                    "old_end_use_detail": "some detail",
                },
            ),
            AuditType.UPDATED_ORGANISATION: AuditFactory(
                verb=AuditType.UPDATED_ORGANISATION,
                payload={
                    "key": "some key",
                    "new": "some name",
                    "old": "some old name",
                },
            ),
            AuditType.UPDATED_SITE: AuditFactory(
                verb=AuditType.UPDATED_SITE,
                payload={
                    "key": "some key",
                    "new": "some name",
                    "old": "some old name",
                },
            ),
            AuditType.UPDATED_SITE_NAME: AuditFactory(
                verb=AuditType.UPDATED_SITE_NAME,
                payload={
                    "key": "some key",
                    "new": "some name",
                    "old": "some old name",
                },
            ),
            AuditType.UPLOAD_APPLICATION_DOCUMENT: AuditFactory(
                verb=AuditType.UPLOAD_APPLICATION_DOCUMENT,
                payload={
                    "file_name": "somefile.txt",
                },
            ),
            AuditType.UPLOAD_CASE_DOCUMENT: AuditFactory(
                verb=AuditType.UPLOAD_CASE_DOCUMENT,
                payload={
                    "file_name": "somefile.txt",
                },
            ),
            AuditType.UPLOAD_PARTY_DOCUMENT: AuditFactory(
                verb=AuditType.UPLOAD_PARTY_DOCUMENT,
                payload={
                    "file_name": "somefile.txt",
                    "party_name": "some party",
                    "party_type": "end_user",
                },
            ),
        }

    @classmethod
    def delete_test_data(cls):
        cls.document_data.delete()
        cls.site.delete()
        cls.organisation.delete()
        cls.address.delete()
        cls.end_user_advisory_query.delete()
        cls.denial.delete()
        cls.party.delete()
        cls.base_user.delete()
        cls.appeal.delete()
        cls.case_note.delete()
        cls.advice.delete()
        cls.ecju_query.delete()
        cls.document.delete()
        cls.firearm_good_details.delete()
        cls.good.delete()
        cls.good_on_application.delete()
        Audit.objects.all().delete()

    def test_users_baseuser_anonymised(self):
        updated_user = BaseUser.objects.get(id=self.base_user.id)
        assert updated_user.first_name != self.base_user.first_name
        assert updated_user.last_name != self.base_user.last_name
        assert updated_user.email != self.base_user.email
        assert updated_user.phone_number != self.base_user.phone_number

    def test_party_anonymised(self):
        updated_party = Party.objects.get(id=self.party.id)
        assert str(self.party.name) != updated_party.name
        assert str(self.party.address) != updated_party.address
        assert str(self.party.website) != updated_party.website
        assert str(self.party.email) != updated_party.email
        assert str(self.party.phone_number) != updated_party.phone_number
        assert str(self.party.signatory_name_euu) != updated_party.signatory_name_euu
        assert str(self.party.details) != updated_party.details

    def test_address_anonymised(self):
        updated_address = Address.objects.get(id=self.address.id)
        assert self.address.address_line_1 != updated_address.address_line_1
        assert self.address.address_line_2 != updated_address.address_line_2
        assert self.address.region != updated_address.region
        assert self.address.postcode != updated_address.postcode
        assert self.address.city != updated_address.city

    def test_external_data_denial_anonymised(self):
        updated_denial = Denial.objects.get(id=self.denial.id)
        assert self.denial.name != updated_denial.name
        assert self.denial.address != updated_denial.address
        assert self.denial.consignee_name != updated_denial.consignee_name

    def test_organisation_anonymised(self):
        updated_organisation = Organisation.objects.get(id=self.organisation.id)
        assert self.organisation.name != updated_organisation.name
        assert str(self.organisation.phone_number) != updated_organisation.phone_number
        assert self.organisation.website != updated_organisation.website
        assert self.organisation.eori_number != updated_organisation.eori_number
        assert self.organisation.sic_number != updated_organisation.sic_number
        assert self.organisation.vat_number != updated_organisation.vat_number
        assert self.organisation.registration_number != updated_organisation.registration_number

    def test_enduser_advisory_query_anonymised(self):
        updated_end_user_advisory = EndUserAdvisoryQuery.objects.get(id=self.end_user_advisory_query.id)
        assert self.end_user_advisory_query.contact_name != updated_end_user_advisory.contact_name
        assert self.end_user_advisory_query.contact_telephone != updated_end_user_advisory.contact_telephone
        assert self.end_user_advisory_query.contact_email != updated_end_user_advisory.contact_email

    def test_site_anonymised(self):
        updated_site = Site.objects.get(id=self.site.id)
        assert self.site.name != updated_site.name

    def test_document_data_excluded(self):
        assert DocumentData.objects.count() == 0

    def test_appeal_anonymised(self):
        updated_appeal = Appeal.objects.get(id=self.appeal.id)
        assert self.appeal.grounds_for_appeal != updated_appeal.grounds_for_appeal

    def test_case_note_anonymised(self):
        updated_case_note = CaseNote.objects.get(id=self.case_note.id)
        assert self.case_note.text != updated_case_note.text

    def test_advice_text_anonymised(self):
        updated_advice = Advice.objects.get(id=self.advice.id)
        assert self.advice.text != updated_advice.text

    def test_advice_note_anonymised(self):
        updated_advice = Advice.objects.get(id=self.advice.id)
        assert self.advice.note != updated_advice.note

    def test_advice_proviso_anonymised(self):
        updated_advice = Advice.objects.get(id=self.advice.id)
        assert self.advice.proviso != updated_advice.proviso

    def test_ecju_query_question_anonymised(self):
        updated_ecju_query = EcjuQuery.objects.get(id=self.ecju_query.id)
        assert self.ecju_query.question != updated_ecju_query.question

    def test_ecju_query_response_anonymised(self):
        updated_ecju_query = EcjuQuery.objects.get(id=self.ecju_query.id)
        assert self.ecju_query.response != updated_ecju_query.response

    def test_document_name_anonymised(self):
        updated_document = Document.objects.get(id=self.document.id)
        assert self.document.name != updated_document.name

    def test_document_s3_key_anonymised(self):
        updated_document = Document.objects.get(id=self.document.id)
        assert self.document.s3_key != updated_document.s3_key

    def test_firearm_good_details_serial_numbers_anonymised(self):
        updated_firearm_good_details = FirearmGoodDetails.objects.get(id=self.firearm_good_details.id)
        for value in self.firearm_good_details.serial_numbers:

            assert value not in updated_firearm_good_details.serial_numbers
        assert len(updated_firearm_good_details.serial_numbers) == len(self.firearm_good_details.serial_numbers)

    def test_firearm_good_details_serial_number_anonymised(self):
        updated_firearm_good_details = FirearmGoodDetails.objects.get(id=self.firearm_good_details.id)

        assert self.firearm_good_details.serial_number != updated_firearm_good_details.serial_number

    def test_good_description_anonymised(self):
        updated_good = Good.objects.get(id=self.good.id)
        assert self.good.description != updated_good.description

    def test_good_on_application_comment_anonymised(self):
        updated_good_on_application = GoodOnApplication.objects.get(id=self.good_on_application.id)

        assert self.good_on_application.comment != updated_good_on_application.comment

    def test_audit_trail_anonymisation_add_case_officer_to_case_anonymised(self):
        previous_audit = self.audit_entries[AuditType.ADD_CASE_OFFICER_TO_CASE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["case_officer"] != previous_audit.payload["case_officer"]

    def test_audit_trail_anonymisation_add_party_anonymised(self):
        previous_audit = self.audit_entries[AuditType.ADD_PARTY]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["party_name"] != previous_audit.payload["party_name"]
        assert updated_audit.payload["party_type"] == previous_audit.payload["party_type"]

    def test_audit_trail_anonymisation_approved_organisation_anonymised(self):
        previous_audit = self.audit_entries[AuditType.APPROVED_ORGANISATION]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["organisation_name"] != previous_audit.payload["organisation_name"]

    def test_audit_trail_anonymisation_assign_user_to_case_anonymised(self):
        previous_audit = self.audit_entries[AuditType.ASSIGN_USER_TO_CASE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["user"] != previous_audit.payload["user"]
        assert updated_audit.payload["additional_text"] == previous_audit.payload["additional_text"]
        assert updated_audit.payload["queue"] == previous_audit.payload["queue"]

    def test_audit_trail_anonymisation_create_refusal_criteria_anonymised(self):
        previous_audit = self.audit_entries[AuditType.CREATE_REFUSAL_CRITERIA]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["firstname"] != previous_audit.payload["firstname"]
        assert updated_audit.payload["lastname"] != previous_audit.payload["lastname"]
        assert updated_audit.payload["additional_text"] == previous_audit.payload["additional_text"]

    def test_audit_trail_anonymisation_created_case_note_anonymised(self):
        previous_audit = self.audit_entries[AuditType.CREATED_CASE_NOTE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        # TODO: Review additional_text..
        assert updated_audit.payload["additional_text"] == previous_audit.payload["additional_text"]

    def test_audit_trail_anonymisation_created_case_note_with_mentions_anonymised(self):
        previous_audit = self.audit_entries[AuditType.CREATED_CASE_NOTE_WITH_MENTIONS]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        # TODO: Review additional_text..
        assert updated_audit.payload["additional_text"] == previous_audit.payload["additional_text"]
        assert updated_audit.payload["mention_users"] != previous_audit.payload["mention_users"]
        assert len(updated_audit.payload["mention_users"]) == len(previous_audit.payload["mention_users"])

    def test_audit_trail_anonymisation_created_organisation_anonymised(self):
        previous_audit = self.audit_entries[AuditType.CREATED_ORGANISATION]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["organisation_name"] != previous_audit.payload["organisation_name"]

    def test_audit_trail_anonymisation_created_site_anonymised(self):
        previous_audit = self.audit_entries[AuditType.CREATED_SITE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["site_name"] != previous_audit.payload["site_name"]

    def test_audit_trail_anonymisation_delete_application_document_anonymised(self):
        previous_audit = self.audit_entries[AuditType.DELETE_APPLICATION_DOCUMENT]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["file_name"] != previous_audit.payload["file_name"]

    def test_audit_trail_anonymisation_delete_party_document_anonymised(self):
        previous_audit = self.audit_entries[AuditType.DELETE_PARTY_DOCUMENT]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["file_name"] != previous_audit.payload["file_name"]
        assert updated_audit.payload["party_name"] != previous_audit.payload["party_name"]
        assert updated_audit.payload["party_type"] == previous_audit.payload["party_type"]

    def test_audit_trail_anonymisation_delete_party_document_anonymised(self):
        previous_audit = self.audit_entries[AuditType.DESTINATION_ADD_FLAGS]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["added_flags"] == previous_audit.payload["added_flags"]
        assert updated_audit.payload["destination_name"] != previous_audit.payload["destination_name"]

    def test_audit_trail_anonymisation_document_on_organisation_create_anonymised(self):
        previous_audit = self.audit_entries[AuditType.DOCUMENT_ON_ORGANISATION_CREATE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["file_name"] != previous_audit.payload["file_name"]
        assert updated_audit.payload["document_type"] == previous_audit.payload["document_type"]

    def test_audit_trail_anonymisation_document_on_organisation_delete_anonymised(self):
        previous_audit = self.audit_entries[AuditType.DOCUMENT_ON_ORGANISATION_DELETE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["file_name"] != previous_audit.payload["file_name"]
        assert updated_audit.payload["document_type"] == previous_audit.payload["document_type"]

    def test_audit_trail_anonymisation_ecju_query_anonymised(self):
        previous_audit = self.audit_entries[AuditType.ECJU_QUERY]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["ecju_query"] != previous_audit.payload["ecju_query"]

    def test_audit_trail_anonymisation_ecju_query_manually_closed_anonymised(self):
        previous_audit = self.audit_entries[AuditType.ECJU_QUERY_MANUALLY_CLOSED]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["ecju_response"] != previous_audit.payload["ecju_response"]

    def test_audit_trail_anonymisation_ecju_query_response_anonymised(self):
        previous_audit = self.audit_entries[AuditType.ECJU_QUERY_RESPONSE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["ecju_response"] != previous_audit.payload["ecju_response"]

    def test_audit_trail_anonymisation_lu_advice_anonymised(self):
        previous_audit = self.audit_entries[AuditType.LU_ADVICE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["firstname"] != previous_audit.payload["firstname"]
        assert updated_audit.payload["lastname"] != previous_audit.payload["lastname"]
        assert updated_audit.payload["advice_type"] == previous_audit.payload["advice_type"]

    def test_audit_trail_anonymisation_lu_countersign_anonymised(self):
        previous_audit = self.audit_entries[AuditType.LU_COUNTERSIGN]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["firstname"] != previous_audit.payload["firstname"]
        assert updated_audit.payload["lastname"] != previous_audit.payload["lastname"]
        assert updated_audit.payload["countersign_accepted"] == previous_audit.payload["countersign_accepted"]
        assert updated_audit.payload["department"] == previous_audit.payload["department"]
        assert updated_audit.payload["order"] == previous_audit.payload["order"]

    def test_audit_trail_anonymisation_lu_create_meeting_note_anonymised(self):
        previous_audit = self.audit_entries[AuditType.LU_CREATE_MEETING_NOTE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["additional_text"] == previous_audit.payload["additional_text"]
        assert updated_audit.payload["advice_type"] == previous_audit.payload["advice_type"]
        assert updated_audit.payload["firstname"] != previous_audit.payload["firstname"]
        assert updated_audit.payload["lastname"] != previous_audit.payload["lastname"]

    def test_audit_trail_anonymisation_lu_edit_advice_anonymised(self):
        previous_audit = self.audit_entries[AuditType.LU_EDIT_ADVICE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["additional_text"] == previous_audit.payload["additional_text"]
        assert updated_audit.payload["advice_type"] == previous_audit.payload["advice_type"]
        assert updated_audit.payload["firstname"] != previous_audit.payload["firstname"]
        assert updated_audit.payload["lastname"] != previous_audit.payload["lastname"]

    def test_audit_trail_anonymisation_lu_edit_meeting_note_anonymised(self):
        previous_audit = self.audit_entries[AuditType.LU_EDIT_MEETING_NOTE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["additional_text"] == previous_audit.payload["additional_text"]
        assert updated_audit.payload["advice_type"] == previous_audit.payload["advice_type"]
        assert updated_audit.payload["firstname"] != previous_audit.payload["firstname"]
        assert updated_audit.payload["lastname"] != previous_audit.payload["lastname"]

    def test_audit_trail_anonymisation_register_organisation_anonymised(self):
        previous_audit = self.audit_entries[AuditType.REGISTER_ORGANISATION]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["organisation_name"] != previous_audit.payload["organisation_name"]
        assert updated_audit.payload["email"] != previous_audit.payload["email"]

    def test_audit_trail_anonymisation_rejected_organisation_anonymised(self):
        previous_audit = self.audit_entries[AuditType.REJECTED_ORGANISATION]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["organisation_name"] != previous_audit.payload["organisation_name"]

    def test_audit_trail_anonymisation_remove_case_officer_from_case_anonymised(self):
        previous_audit = self.audit_entries[AuditType.REMOVE_CASE_OFFICER_FROM_CASE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["case_officer"] != previous_audit.payload["case_officer"]

    def test_audit_trail_anonymisation_remove_party_anonymised(self):
        previous_audit = self.audit_entries[AuditType.REMOVE_PARTY]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["party_name"] != previous_audit.payload["party_name"]
        assert updated_audit.payload["party_type"] == previous_audit.payload["party_type"]

    def test_audit_trail_anonymisation_remove_user_from_case_anonymised(self):
        previous_audit = self.audit_entries[AuditType.REMOVE_USER_FROM_CASE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["removed_user_name"] != previous_audit.payload["removed_user_name"]
        assert updated_audit.payload["removed_user_id"] == previous_audit.payload["removed_user_id"]
        assert updated_audit.payload["removed_user_queue_id"] == previous_audit.payload["removed_user_queue_id"]
        assert updated_audit.payload["removed_user_queue_name"] == previous_audit.payload["removed_user_queue_name"]

    def test_audit_trail_anonymisation_update_application_end_use_detail(self):
        previous_audit = self.audit_entries[AuditType.UPDATE_APPLICATION_END_USE_DETAIL]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["new_end_use_detail"] != previous_audit.payload["new_end_use_detail"]
        assert updated_audit.payload["old_end_use_detail"] != previous_audit.payload["old_end_use_detail"]
        assert updated_audit.payload["end_use_detail"] == previous_audit.payload["end_use_detail"]

    def test_audit_trail_anonymisation_updated_organisation_anonymised(self):
        previous_audit = self.audit_entries[AuditType.UPDATED_ORGANISATION]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["new"] != previous_audit.payload["new"]
        assert updated_audit.payload["old"] != previous_audit.payload["old"]
        assert updated_audit.payload["key"] == previous_audit.payload["key"]

    def test_audit_trail_anonymisation_updated_site_anonymised(self):
        previous_audit = self.audit_entries[AuditType.UPDATED_SITE]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["new"] != previous_audit.payload["new"]
        assert updated_audit.payload["old"] != previous_audit.payload["old"]
        assert updated_audit.payload["key"] == previous_audit.payload["key"]

    def test_audit_trail_anonymisation_updated_site_name(self):
        previous_audit = self.audit_entries[AuditType.UPDATED_SITE_NAME]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["new"] != previous_audit.payload["new"]
        assert updated_audit.payload["old"] != previous_audit.payload["old"]
        assert updated_audit.payload["key"] == previous_audit.payload["key"]

    def test_audit_trail_anonymisation_upload_application_document(self):
        previous_audit = self.audit_entries[AuditType.UPLOAD_APPLICATION_DOCUMENT]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["file_name"] != previous_audit.payload["file_name"]

    def test_audit_trail_anonymisation_upload_case_document(self):
        previous_audit = self.audit_entries[AuditType.UPLOAD_CASE_DOCUMENT]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["file_name"] != previous_audit.payload["file_name"]

    def test_audit_trail_anonymisation_upload_party_document(self):
        previous_audit = self.audit_entries[AuditType.UPLOAD_PARTY_DOCUMENT]
        updated_audit = Audit.objects.get(id=previous_audit.id)
        assert updated_audit.payload["file_name"] != previous_audit.payload["file_name"]
        assert updated_audit.payload["party_name"] != previous_audit.payload["party_name"]
        assert updated_audit.payload["party_type"] == previous_audit.payload["party_type"]
