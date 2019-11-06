from django.urls import reverse
from rest_framework import status

from applications.models import (
    StandardApplication,
    SiteOnApplication,
    ExternalLocationOnApplication,
)
from test_helpers.clients import DataTestClient


class SitesOnDraftTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.primary_site = self.organisation.primary_site
        self.application = self.create_standard_application(self.organisation)

        self.url = reverse(
            "applications:application_sites", kwargs={"pk": self.application.id}
        )

    def test_add_site_to_a_draft(self):
        data = {"sites": [self.primary_site.id]}

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.application = StandardApplication.objects.get(pk=self.application.id)
        self.assertEqual(self.application.activity, "Trading")

        url = reverse(
            "applications:application_sites", kwargs={"pk": self.application.id}
        )
        response = self.client.get(url, **self.exporter_headers).json()
        self.assertEqual(len(response["sites"]), 1)

    def test_add_multiple_sites_to_a_draft(self):
        site2, address = self.create_site("site2", self.organisation)

        data = {"sites": [self.primary_site.id, site2.id]}

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.application = StandardApplication.objects.get(pk=self.application.id)
        self.assertEqual(self.application.activity, "Trading")

        url = reverse(
            "applications:application_sites", kwargs={"pk": self.application.id}
        )
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()
        self.assertEqual(len(response_data["sites"]), 2)

    def test_user_cannot_add_another_organisations_site_to_a_draft(self):
        org2 = self.create_organisation_with_exporter_user()
        site_org2 = org2.primary_site

        data = {"sites": [site_org2.id]}

        url = reverse(
            "applications:application_sites", kwargs={"pk": self.application.id}
        )
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse(
            "applications:application_sites", kwargs={"pk": self.application.id}
        )
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(len(response_data["sites"]), 1)

    def test_add_a_site_to_a_draft_deletes_existing_sites(self):
        url = reverse(
            "applications:application_sites", kwargs={"pk": self.application.id}
        )
        response = self.client.get(url, **self.exporter_headers).json()

        site_id = response["sites"][0]["id"]
        self.assertEqual(len(response["sites"]), 1)

        # Post a new site to the draft, with the expectation that the existing site is deleted
        data = {"sites": [str(self.create_site("New Site", self.organisation)[0].id)]}

        url = reverse(
            "applications:application_sites", kwargs={"pk": self.application.id}
        )
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that the new site has been added, and the old one deleted
        url = reverse(
            "applications:application_sites", kwargs={"pk": self.application.id}
        )
        response = self.client.get(url, **self.exporter_headers).json()
        self.assertEqual(len(response["sites"]), 1)
        self.assertNotEqual(response["sites"][0]["id"], site_id)

    def test_adding_site_to_draft_deletes_external_locations(self):
        draft = self.application
        external_location = self.create_external_location("test", self.organisation)
        url = reverse(
            "applications:application_sites", kwargs={"pk": self.application.id}
        )
        data = {"external_locations": [external_location.id]}
        self.client.post(url, data, **self.exporter_headers)
        data = {"sites": [self.primary_site.id]}
        self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(SiteOnApplication.objects.filter(application=draft).count(), 1)
        self.assertEqual(
            ExternalLocationOnApplication.objects.filter(application=draft).count(), 0
        )

    def test_add_site_to_a_submitted_application_success(self):
        site_to_add, _ = self.create_site("site 2", self.organisation)
        data = {"sites": [self.primary_site.id, site_to_add.id]}
        self.submit_application(self.application)

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            SiteOnApplication.objects.filter(application=self.application).count(), 2
        )

    def test_add_site_to_a_submitted_application_failure(self):
        """
        Cannot add additional site to a submitted application unless the additional site
        is located in a country that is already on the application
        """
        site_to_add, _ = self.create_site("site 2", self.organisation, "US")
        data = {"sites": [self.primary_site.id, site_to_add.id]}
        self.submit_application(self.application)

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            SiteOnApplication.objects.filter(application=self.application).count(), 1
        )

    def test_adding_site_to_submitted_application_when_external_locations_already_on_application_failure(
        self,
    ):
        SiteOnApplication.objects.filter(application=self.application).delete()
        external_location = self.create_external_location(
            "storage facility", self.organisation
        )
        ExternalLocationOnApplication(
            application=self.application, external_location=external_location
        ).save()

        self.submit_application(self.application)
        data = {"sites": [self.primary_site.id]}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            SiteOnApplication.objects.filter(application=self.application).count(), 0
        )
        self.assertEqual(
            ExternalLocationOnApplication.objects.filter(
                application=self.application
            ).count(),
            1,
        )
