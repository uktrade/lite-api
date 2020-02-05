from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy

from applications.enums import (
    ApplicationType,
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
)
from applications.models import (
    StandardApplication,
    OpenApplication,
    HmrcQuery,
    BaseApplication,
    ExhibitionClearanceApplication,
)
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient


class DraftCopyTests(DataTestClient):

    # standard application
    def test_copy_draft_standard_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_standard_application(self.organisation)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

    def test_copy_submitted_standard_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_standard_application_case(self.organisation)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

    def test_copy_draft_open_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_open_application(self.organisation)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

    def test_copy_submitted_open_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_open_application(self.organisation)
        self.submit_application(application)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

    def test_copy_draft_exhibition_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_exhibition_clearance_application(self.organisation)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

    def test_copy_submitted_exhibition_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_exhibition_clearance_application(self.organisation)
        self.submit_application(application)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)
