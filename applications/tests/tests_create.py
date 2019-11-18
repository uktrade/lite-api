from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from applications.enums import (
    ApplicationType,
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
)
from applications.models import StandardApplication, OpenApplication, HmrcQuery
from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):

    url = reverse("applications:applications")

    def test_create_draft_standard_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        data = {
            "name": "Test",
            "application_type": ApplicationType.STANDARD_LICENCE,
            "export_type": ApplicationExportType.TEMPORARY,
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "123",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StandardApplication.objects.count(), 1)

    def test_create_draft_open_application_successful(self):
        """
        Ensure we can create a new open application draft object
        """
        data = {
            "name": "Test",
            "application_type": ApplicationType.OPEN_LICENCE,
            "export_type": ApplicationExportType.TEMPORARY,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OpenApplication.objects.count(), 1)

    def test_create_draft_hmrc_query_successful(self):
        """
        Ensure we can create a new HMRC query draft object
        """
        data = {
            "application_type": ApplicationType.HMRC_QUERY,
            "organisation": self.organisation.id,
        }

        response = self.client.post(self.url, data, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HmrcQuery.objects.count(), 1)

    def test_create_draft_hmrc_query_failure(self):
        """
        Ensure that a normal exporter cannot create an HMRC query
        """
        data = {
            "application_type": "hmrc_query",
            "organisation": self.organisation.id,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(HmrcQuery.objects.count(), 0)

    @parameterized.expand(
        [
            [{}],
            [{"application_type": "standard_licence", "export_type": "temporary",}],
            [{"name": "Test", "export_type": "temporary",}],
            [{"name": "Test", "application_type": "standard_licence",}],
        ]
    )
    def test_create_draft_failure(self, data):
        """
        Ensure we cannot create a new draft object with an invalid POST
        """
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(OpenApplication.objects.count(), 0)
