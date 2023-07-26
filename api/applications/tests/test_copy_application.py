from uuid import uuid4

from rest_framework import status
from rest_framework.reverse import reverse_lazy

from api.applications.enums import ApplicationExportLicenceOfficialType, ApplicationExportType
from api.applications.models import (
    StandardApplication,
    GoodOnApplication,
    CountryOnApplication,
    SiteOnApplication,
)
from api.cases.enums import CaseTypeSubTypeEnum
from api.parties.models import PartyDocument
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class CopyApplicationSuccessTests(DataTestClient):
    # standard application
    def test_copy_draft_standard_application_successful(self):
        """
        Ensure we can copy a standard application that is a draft
        """
        self.original_application = self.create_draft_standard_application(self.organisation, ultimate_end_users=True)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {
            "name": "New application",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "54321-12",
        }

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self._validate_standard_application()

    def test_copy_draft_standard_temporary_application_successful(self):
        """
        Ensure we can copy a standard temporary application that is a draft
        """
        self.original_application = self.create_draft_standard_application(self.organisation)
        self.original_application.export_type = ApplicationExportType.TEMPORARY
        self.original_application.temp_export_details = "temporary export details"
        self.original_application.is_temp_direct_control = True
        self.original_application.proposed_return_date = "2025-05-11"
        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {
            "name": "New application",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "54321-12",
        }

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self._validate_standard_application()

    def test_copy_submitted_standard_application_successful(self):
        """
        Ensure we can copy a standard application that has been submitted (ongoing or not)
        """
        self.original_application = self.create_standard_application_case(self.organisation)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {
            "name": "New application",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "54321-12",
        }

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self._validate_standard_application()

    def test_copy_submitted_standard_temporary_application_successful(self):
        """
        Ensure we can copy a standard temporary application that has been submitted (ongoing or not)
        """
        self.original_application = self.create_draft_standard_application(self.organisation)
        self.original_application.export_type = ApplicationExportType.TEMPORARY
        self.original_application.temp_export_details = "temporary export details"
        self.original_application.is_temp_direct_control = True
        self.original_application.proposed_return_date = "2025-05-11"

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {
            "name": "New application",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "54321-12",
        }

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self._validate_standard_application()

    def _validate_standard_application(self):
        self._validate_reset_data()
        self._validate_end_use_details()
        self._validate_good_on_application()
        self._validate_end_user()
        self._validate_consignee()
        self._validate_ultimate_end_user()
        self._validate_third_party()
        self._validate_case_data()
        self._validate_route_of_goods()
        self._validate_temporary_export_details()

    def _validate_reset_data(self):
        self.assertNotEqual(self.copied_application.id, self.original_application.id)
        self.assertEqual(self.copied_application.copy_of.id, self.original_application.id)
        self.assertEqual(self.copied_application.status, get_case_status_by_status(CaseStatusEnum.DRAFT))
        self.assertGreater(self.copied_application.created_at, self.original_application.created_at)
        self.assertGreater(self.copied_application.updated_at, self.original_application.updated_at)

    def _validate_end_use_details(self, application_type=None):
        if application_type in [CaseTypeSubTypeEnum.STANDARD]:
            self.assertIsNone(self.copied_application.intended_end_use)
            self.assertIsNone(self.copied_application.is_informed_wmd)
            self.assertIsNone(self.copied_application.is_suspected_wmd)
            self.assertIsNone(self.copied_application.is_military_end_use_controls)
            if application_type == CaseTypeSubTypeEnum.STANDARD:
                self.assertIsNone(self.copied_application.is_eu_military)
                self.assertIsNone(self.copied_application.is_compliant_limitations_eu)
                self.assertIsNone(self.copied_application.compliant_limitations_eu_ref)

    def _validate_route_of_goods(self):
        self.assertIsNone(self.copied_application.is_shipped_waybill_or_lading)
        self.assertIsNone(self.copied_application.non_waybill_or_lading_route_details)

    def _validate_temporary_export_details(self, export_type=None):
        if export_type == ApplicationExportType.TEMPORARY:
            self.assertIsNone(self.copied_application.temp_export_details)
            self.assertIsNone(self.copied_application.is_temp_direct_control)
            self.assertIsNone(self.copied_application.temp_direct_control_details)
            self.assertIsNone(self.copied_application.proposed_return_date)

    def _validate_good_on_application(self):
        new_goods_on_app = self.copied_application.goods.all()
        original_goods_on_app = self.original_application.goods.all()
        for good_on_app in original_goods_on_app:
            self.assertNotIn(good_on_app, new_goods_on_app)

            new_good_on_app = GoodOnApplication.objects.get(
                application_id=self.original_application.id, good_id=good_on_app.good.id
            )

            self.assertEqual(good_on_app.good, new_good_on_app.good)
            self.assertEqual(good_on_app.value, new_good_on_app.value)
            self.assertEqual(good_on_app.quantity, new_good_on_app.quantity)
            self.assertEqual(good_on_app.unit, new_good_on_app.unit)

        self.assertEqual(len(new_goods_on_app), len(original_goods_on_app))

    def _validate_party_details(self, new_party, original_party):
        self.assertNotEqual(new_party.id, original_party.id)
        self.assertGreater(new_party.created_at, original_party.created_at)
        self.assertGreater(new_party.updated_at, original_party.updated_at)
        self.assertEqual(new_party.name, original_party.name)
        self.assertEqual(new_party.address, original_party.address)
        self.assertEqual(new_party.country, original_party.country)
        self.assertEqual(new_party.type, original_party.type)
        self.assertEqual(new_party.sub_type, original_party.sub_type)
        self.assertEqual(list(PartyDocument.objects.filter(party=new_party).all()), [])

    def _validate_end_user(self):
        self.assertIsNotNone(self.copied_application.end_user)
        self._validate_party_details(self.copied_application.end_user.party, self.original_application.end_user.party)

    def _validate_consignee(self):
        self.assertIsNotNone(self.copied_application.consignee)
        self._validate_party_details(self.copied_application.consignee.party, self.original_application.consignee.party)

    def _validate_ultimate_end_user(self):
        self.assertIsNotNone(self.copied_application.ultimate_end_users)
        ultimate_end_users = self.copied_application.ultimate_end_users.all()
        original_ultimate_end_users = [user.party for user in self.original_application.ultimate_end_users.all()]
        self.assertEqual(len(ultimate_end_users), len(original_ultimate_end_users))
        for ueu in ultimate_end_users:
            self.assertNotIn(ueu.party, original_ultimate_end_users)
            original_ueu = [user for user in original_ultimate_end_users if user.name == ueu.party.name][0]
            self._validate_party_details(ueu.party, original_ueu)

    def _validate_third_party(self):
        self.assertIsNotNone(self.copied_application.third_parties)
        third_parties = self.copied_application.third_parties.all()
        original_third_parties = [user.party for user in self.original_application.third_parties.all()]
        self.assertEqual(len(third_parties), len(original_third_parties))
        for third_party in third_parties:
            self.assertNotIn(third_party.party, original_third_parties)
            original_ueu = [user for user in original_third_parties if user.name == third_party.party.name][0]
            self._validate_party_details(third_party.party, original_ueu)

    def _validate_case_data(self):
        self.assertEqual(list(self.copied_application.case_ecju_query.all()), [])
        self.assertEqual(list(self.copied_application.case_notes.all()), [])
        self.assertEqual(list(self.copied_application.goodcountrydecision_set.all()), [])
        self.assertEqual(list(self.copied_application.get_case().advice.all()), [])
        self.assertEqual(list(self.copied_application.applicationdocument_set.all()), [])
        self.assertEqual(list(self.copied_application.casedocument_set.all()), [])

    def _validate_country_on_application(self):
        self.assertIsNotNone(self.copied_application.application_countries)
        new_countries = list(
            CountryOnApplication.objects.filter(application=self.copied_application).values("country").all()
        )
        for country in (
            CountryOnApplication.objects.filter(application=self.original_application).values("country").all()
        ):
            self.assertIn(country, new_countries)

    def _validate_site_on_application(self):
        self.assertIsNotNone(self.copied_application.application_sites)
        new_sites = list(SiteOnApplication.objects.filter(application=self.copied_application).values("site").all())
        old_sites = SiteOnApplication.objects.filter(application=self.original_application).values("site").all()
        self.assertEqual(len(new_sites), len(old_sites))
        for site in old_sites:
            self.assertIn(site, new_sites)


class CopyApplicationFailTests(DataTestClient):
    def test_copy_bad_pk(self):
        self.url = reverse_lazy("applications:copy", kwargs={"pk": uuid4()})
        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(self.response.status_code, status.HTTP_404_NOT_FOUND)

    # standard
    def test_copy_standard_application_missing_data_informed(self):
        """
        Ensure we can copy a standard application that is a draft
        """
        self.original_application = self.create_draft_standard_application(self.organisation)
        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})
        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(self.response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_copy_missing_data_name(self):
        """
        Ensure we can copy a standard application that is a draft
        """
        self.original_application = self.create_draft_standard_application(self.organisation)
        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})
        self.data = {"have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(self.response.status_code, status.HTTP_400_BAD_REQUEST)
