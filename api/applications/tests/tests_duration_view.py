from django.urls import reverse

from api.applications.enums import ApplicationExportType, DefaultDuration
from api.applications.models import CountryOnApplication
from test_helpers.clients import DataTestClient


class DurationViewTest(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.open_application = self.create_draft_open_application(self.organisation)
        self.submit_application(self.standard_application)
        self.submit_application(self.open_application)

    def test_get_open_licence_duration_non_eu(self):
        url = reverse("applications:duration", kwargs={"pk": self.open_application.pk})

        country = CountryOnApplication.objects.get(application=self.open_application).country

        # Non eu
        country.is_eu = False
        country.save()
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.json()["licence_duration"], DefaultDuration.PERMANENT_OPEN.value)

    def test_get_open_licence_duration_non_eu(self):
        url = reverse("applications:duration", kwargs={"pk": self.open_application.pk})

        country = CountryOnApplication.objects.get(application=self.open_application).country

        # eu
        country.is_eu = True
        country.save()
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.json()["licence_duration"], DefaultDuration.PERMANENT_OPEN_EU.value)

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
