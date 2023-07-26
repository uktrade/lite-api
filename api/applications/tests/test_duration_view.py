from django.urls import reverse

from api.applications.enums import ApplicationExportType, DefaultDuration
from test_helpers.clients import DataTestClient


class DurationViewTest(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.standard_application)

    def test_get_standard_licence_duration(self):
        url = reverse("applications:duration", kwargs={"pk": self.standard_application.pk})
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.json()["licence_duration"], DefaultDuration.PERMANENT_STANDARD.value)

    def test_temporary_licence_duration(self):
        self.standard_application.export_type = ApplicationExportType.TEMPORARY
        self.standard_application.save()

        url = reverse("applications:duration", kwargs={"pk": self.standard_application.pk})
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.json()["licence_duration"], DefaultDuration.TEMPORARY.value)
