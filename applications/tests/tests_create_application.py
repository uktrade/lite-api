from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

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

    def test_create_draft_exhibition_clearance_application_successful(self):
        """
        Ensure we can create a new Exhibition Clearance draft object
        """
        self.assertEqual(ExhibitionClearanceApplication.objects.count(), 0)

        data = {
            "name": "Test",
            "application_type": ApplicationType.EXHIBITION_CLEARANCE,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExhibitionClearanceApplication.objects.count(), 1)

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
            [{"application_type": ApplicationType.STANDARD_LICENCE, "export_type": ApplicationExportType.TEMPORARY,}],
            [{"name": "Test", "export_type": ApplicationExportType.TEMPORARY,}],
            [{"name": "Test", "application_type": ApplicationType.STANDARD_LICENCE,}],
            [{"application_type": ApplicationType.EXHIBITION_CLEARANCE,}],
            [{"name": "Test",}],
        ]
    )
    def test_create_draft_failure(self, data):
        """
        Ensure we cannot create a new draft object with an invalid POST
        """
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(BaseApplication.objects.count(), 0)

    def test_create_no_application_type_failure(self):
        """
        Ensure that we cannot create a new application without
        providing a licence type.
        """
        data = {}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"]["application_type"][0], strings.Applications.SELECT_A_LICENCE_TYPE)
