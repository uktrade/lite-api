from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.applications.libraries.case_status_helpers import get_case_statuses
from api.applications.tests.factories import CryptoOIELFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class EditStandardApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.data = {"name": "new app name!"}

    def test_edit_unsubmitted_application_name_success(self):
        """Test edit the application name of an unsubmitted application. An unsubmitted application
        has the 'draft' status.
        """
        application = self.create_draft_standard_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at

        response = self.client.put(url, self.data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, self.data["name"])
        self.assertGreater(application.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    def test_edit_unsubmitted_application_export_type_success(self):
        """Test edit the application export_type of an unsubmitted application. An unsubmitted application
        has the 'draft' status.
        """
        application = self.create_draft_standard_application(self.organisation)
        # export_type is set to permanent in create_draft_standard_application
        self.assertEqual(application.export_type, "permanent")

        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at

        response = self.client.put(url, {"export_type": "temporary"}, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.export_type, "temporary")
        self.assertGreater(application.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    def test_edit_unsubmitted_application_locations_success(self):
        application = self.create_draft_standard_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at

        data = {
            "goods_starting_point": "GB",
            "goods_recipients": "via_consignee",
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.goods_starting_point, "GB")
        self.assertEqual(application.goods_recipients, "via_consignee")
        self.assertGreater(application.updated_at, updated_at)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.count(), 0)

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_edit_application_name_in_editable_status_success(self, editable_status):
        old_name = "Old Name"
        application = self.create_draft_standard_application(self.organisation, reference_name=old_name)
        self.submit_application(application)
        application.status = get_case_status_by_status(editable_status)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at
        response = self.client.put(url, self.data, **self.exporter_headers)
        application.refresh_from_db()
        audit_object = Audit.objects.get(verb=AuditType.UPDATED_APPLICATION_NAME)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, self.data["name"])
        self.assertNotEqual(application.updated_at, updated_at)
        self.assertEqual(audit_object.payload, {"new_name": self.data["name"], "old_name": old_name})

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_edit_application_name_in_read_only_status_failure(self, read_only_status):
        application = self.create_draft_standard_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(read_only_status)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})

        response = self.client.put(url, self.data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_submitted_application_reference_number(self):
        """Test successful editing of an application's reference number when the application's status
        is non read-only.
        """
        application = self.create_draft_standard_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})
        updated_at = application.updated_at
        new_ref = "35236246"
        update_ref = "13124124"

        # Add ref
        data = {"reference_number_on_information_form": new_ref, "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            application.reference_number_on_information_form,
            data["reference_number_on_information_form"],
        )
        self.assertNotEqual(application.updated_at, updated_at)

        # Check add audit
        audit = Audit.objects.get(verb=AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit.payload, {"old_ref_number": "no reference", "new_ref_number": new_ref})

        # Update ref
        data = {"reference_number_on_information_form": update_ref, "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update audit
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        audit = Audit.objects.filter(verb=AuditType.UPDATE_APPLICATION_LETTER_REFERENCE).first()
        self.assertEqual(audit.payload, {"old_ref_number": new_ref, "new_ref_number": update_ref})

        # Update ref with no reference
        data = {"reference_number_on_information_form": "", "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        audit = Audit.objects.filter(verb=AuditType.UPDATE_APPLICATION_LETTER_REFERENCE).first()
        self.assertEqual(audit.payload, {"old_ref_number": update_ref, "new_ref_number": "no reference"})

        # Remove ref
        data = {"reference_number_on_information_form": "", "have_you_been_informed": "no"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        audit = Audit.objects.get(verb=AuditType.REMOVED_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit.payload, {"old_ref_number": "no reference"})


class EditCryptoOpenApplicationTests(DataTestClient):
    def test_edit_unsubmitted_crypto_application_name_success(self):
        application = CryptoOIELFactory(organisation=self.organisation)

        url = reverse("applications:application", kwargs={"pk": application.id})

        response = self.client.put(url, {"name": "Crypto OIEL"}, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, "Crypto OIEL")

    def test_crypto_application_edit_additional_info(self):
        application = CryptoOIELFactory(organisation=self.organisation)

        url = reverse("applications:application", kwargs={"pk": application.id})
        data = {
            "nature_of_products": "Cryptographic products",
            "siels_issued_last_year": True,
            "number_of_siels_last_year": 5,
            "destination_countries": "Australia, Japan",
            "purely_commercial": True,
        }

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.nature_of_products, "Cryptographic products")
        self.assertTrue(application.siels_issued_last_year)
        self.assertEqual(application.number_of_siels_last_year, "5")
        self.assertEqual(application.destination_countries, "Australia, Japan")
        self.assertTrue(application.purely_commercial)
