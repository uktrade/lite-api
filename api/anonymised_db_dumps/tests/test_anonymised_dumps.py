import os
from datetime import datetime

from django.conf import settings
from django.core.management import call_command
from django.test import TransactionTestCase

from api.document_data.models import DocumentData
from api.organisations.tests.factories import SiteFactory, OrganisationFactory
from api.addresses.tests.factories import AddressFactory
from api.staticdata.countries.models import Country
from api.queries.end_user_advisories.tests.factories import EndUserAdvisoryQueryFactory
from api.external_data.tests.factories import DenialFactory
from api.parties.tests.factories import PartyFactory
from api.users.tests.factories import BaseUserFactory


class TestAnonymiseDumps(TransactionTestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.delete_test_data()

    @classmethod
    def create_test_data(cls):
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

    def test_users_baseuser_anonymised(self):
        assert str(self.base_user.id) in self.anonymised_sql
        assert str(self.base_user.first_name) not in self.anonymised_sql
        assert str(self.base_user.last_name) not in self.anonymised_sql
        assert str(self.base_user.email) not in self.anonymised_sql
        assert str(self.base_user.phone_number) not in self.anonymised_sql

    def test_party_anonymised(self):
        assert str(self.party.id) in self.anonymised_sql
        assert str(self.party.name) not in self.anonymised_sql
        assert str(self.party.address) not in self.anonymised_sql
        assert str(self.party.website) not in self.anonymised_sql
        assert str(self.party.email) not in self.anonymised_sql
        assert str(self.party.phone_number) not in self.anonymised_sql
        assert str(self.party.signatory_name_euu) not in self.anonymised_sql
        assert str(self.party.details) not in self.anonymised_sql

    def test_address_anonymised(self):
        assert str(self.address.id) in self.anonymised_sql
        assert self.address.address_line_1 not in self.anonymised_sql
        assert self.address.address_line_2 not in self.anonymised_sql
        assert self.address.region not in self.anonymised_sql
        assert self.address.postcode not in self.anonymised_sql
        assert self.address.city not in self.anonymised_sql

    def test_external_data_denial_anonymised(self):
        assert str(self.denial.id) in self.anonymised_sql
        assert self.denial.name not in self.anonymised_sql
        assert self.denial.address not in self.anonymised_sql
        assert self.denial.consignee_name not in self.anonymised_sql

    def test_organisation_anonymised(self):
        assert str(self.organisation.id) in self.anonymised_sql
        assert self.organisation.name not in self.anonymised_sql
        assert str(self.organisation.phone_number) not in self.anonymised_sql
        assert self.organisation.website not in self.anonymised_sql
        assert self.organisation.eori_number not in self.anonymised_sql
        assert self.organisation.sic_number not in self.anonymised_sql
        assert self.organisation.vat_number not in self.anonymised_sql
        assert self.organisation.registration_number not in self.anonymised_sql

    def test_enduser_advisory_query_anonymised(self):
        assert str(self.end_user_advisory_query.id) in self.anonymised_sql
        assert self.end_user_advisory_query.contact_name not in self.anonymised_sql
        assert self.end_user_advisory_query.contact_telephone not in self.anonymised_sql
        assert self.end_user_advisory_query.contact_email not in self.anonymised_sql

    def test_site_anonymised(self):
        assert str(self.site.id) in self.anonymised_sql
        assert self.site.name not in self.anonymised_sql

    def test_document_data_excluded(self):
        assert self.document_data.s3_key not in self.anonymised_sql
        assert str(self.document_data.id) not in self.anonymised_sql
