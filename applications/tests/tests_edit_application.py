from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.libraries.case_status_helpers import get_case_statuses
from audit_trail.models import Audit
from audit_trail.payload import AuditType
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class EditApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.data = {"name": "new app name!"}

    def test_edit_unsubmitted_application_name_success(self):
        """ Test edit the application name of an unsubmitted application. An unsubmitted application
        has the 'draft' status.
        """
        application = self.create_standard_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": application.id})
        modified = application.modified

        response = self.client.put(url, self.data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, self.data["name"])
        self.assertNotEqual(application.modified, modified)
        # Unsubmitted (draft) applications should not create audit entries when edited
        self.assertEqual(Audit.objects.all().count(), 0)

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_edit_application_name_in_editable_status_success(self, editable_status):
        old_name = "Old Name"
        application = self.create_standard_application(self.organisation, reference_name=old_name)
        self.submit_application(application)
        application.status = get_case_status_by_status(editable_status)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})
        modified = application.modified
        response = self.client.put(url, self.data, **self.exporter_headers)
        application.refresh_from_db()
        audit_qs = Audit.objects.all()
        audit_object = audit_qs.first()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, self.data["name"])
        self.assertNotEqual(application.modified, modified)
        self.assertEqual(audit_qs.count(), 1)
        self.assertEqual(audit_object.payload, {"new_name": self.data["name"], "old_name": old_name})

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_edit_application_name_in_read_only_status_failure(self, read_only_status):
        application = self.create_standard_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(read_only_status)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})

        response = self.client.put(url, self.data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_submitted_application_reference_number(self):
        """ Test successful editing of an application's reference number when the application's status
        is non read-only.
        """
        application = self.create_standard_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})
        modified = application.modified
        audit_qs = Audit.objects.all()
        new_ref = "35236246"
        update_ref = "13124124"

        # Add ref
        data = {"reference_number_on_information_form": new_ref, "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            application.reference_number_on_information_form, data["reference_number_on_information_form"],
        )
        self.assertNotEqual(application.modified, modified)

        # Check add audit
        self.assertEqual(audit_qs.count(), 1)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": "no reference", "new_ref_number": new_ref})

        # Update ref
        data = {"reference_number_on_information_form": update_ref, "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update audit
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_qs.count(), 2)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": new_ref, "new_ref_number": update_ref})

        # Update ref with no reference
        data = {"reference_number_on_information_form": "", "have_you_been_informed": "yes"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_qs.count(), 3)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.UPDATE_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": update_ref, "new_ref_number": "no reference"})

        # Remove ref
        data = {"reference_number_on_information_form": "", "have_you_been_informed": "no"}
        response = self.client.put(url, data, **self.exporter_headers)

        # Check update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_qs.count(), 4)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.REMOVED_APPLICATION_LETTER_REFERENCE)
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": "no reference"})
