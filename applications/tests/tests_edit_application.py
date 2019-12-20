from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.libraries.case_status_helpers import get_case_statuses
from audit_trail.models import Audit
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
        application = self.create_standard_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_by_status(editable_status)
        application.save()
        url = reverse("applications:application", kwargs={"pk": application.id})
        modified = application.modified

        response = self.client.put(url, self.data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, self.data["name"])
        self.assertNotEqual(application.modified, modified)

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

        data = {"reference_number_on_information_form": "35236246"}

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            application.reference_number_on_information_form, data["reference_number_on_information_form"],
        )
        self.assertNotEqual(application.modified, modified)
        # Editable status applications (other than draft) should create audit entries when edited
        self.assertEqual(Audit.objects.all().count(), 1)
