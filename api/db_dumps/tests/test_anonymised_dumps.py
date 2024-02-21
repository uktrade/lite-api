import os
from datetime import datetime

from django.core.management import call_command
from django.test import TransactionTestCase

from api.document_data.models import DocumentData
from api.organisations.tests.factories import SiteFactory, OrganisationFactory


class TestAnonymiseDumps(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        cls.create_test_data()
        try:
            os.remove("/tmp/anonymised.sql")
        except FileNotFoundError:
            pass
        call_command("dump_and_anonymise", keep_local_dumpfile=True, skip_s3_upload=True)
        with open("/tmp/anonymised.sql", "r") as f:
            cls.anonymised_sql = f.read()

    @classmethod
    def create_test_data(cls):
        cls.document_data = DocumentData.objects.create(
            s3_key="somefile.txt", content_type="csv", last_modified=datetime.now()
        )
        cls.site = SiteFactory(name="some site")
        cls.organisation = OrganisationFactory(
            name="some org",
            phone_number="+4466",
            website="someexample.net",
            eori_number="some_eori",
            sic_number="some_sic",
            vat_number="some_vat",
            registration_number="some_reg",
        )

    def test_document_data_excluded(self):
        assert "somefile.txt" not in self.anonymised_sql
        assert str(self.document_data.id) not in self.anonymised_sql

    def test_site_anonymised(self):
        assert str(self.site.id) in self.anonymised_sql
        assert self.site.name not in self.anonymised_sql

    def test_organisation_anonymised(self):
        assert str(self.organisation.id) in self.anonymised_sql
        assert self.organisation.name not in self.anonymised_sql
        assert str(self.organisation.phone_number) not in self.anonymised_sql
        assert self.organisation.website not in self.anonymised_sql
        assert self.organisation.eori_number not in self.anonymised_sql
        assert self.organisation.sic_number not in self.anonymised_sql
        assert self.organisation.vat_number not in self.anonymised_sql
        assert self.organisation.registration_number not in self.anonymised_sql
