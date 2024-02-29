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
