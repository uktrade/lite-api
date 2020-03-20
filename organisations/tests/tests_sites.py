from rest_framework import status
from rest_framework.reverse import reverse

from organisations.models import Site
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class OrganisationSitesTests(DataTestClient):
    def test_site_list(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        # Create an additional organisation and site to ensure
        # that only sites from the first organisation are shown
        self.create_organisation_with_exporter_user("New Org")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["sites"]), 1)
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_add_uk_site(self):
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "address": {
                "address_line_1": "a street",
                "city": "london",
                "postcode": "E14GH",
                "region": "Hertfordshire",
            },
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 2)

    def test_add_foreign_site(self):
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "foreign_address": {"address": "a street", "country": "PL",},
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 2)

    def test_add_foreign_site_failure(self):
        # TODO Adding a foreign site but syaing the country is in the uk
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "foreign_address": {"address": "a street", "country": "GB",},
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 1)

    def test_add_foreign_site_failure2(self):
        # TODO Adding a foreign site but syaing the country is in the uk
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "address": {
                "address_line_1": "a street",
                "city": "london",
                "postcode": "E14GH",
                "region": "Hertfordshire",
                "country": "GB",
            },
            "foreign_address": {"address": "a street", "country": "PL",},
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 1)

    def test_edit_site(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        url = reverse(
            "organisations:site", kwargs={"org_pk": self.organisation.id, "site_pk": self.organisation.primary_site.id}
        )

        data = {
            "name": "regional site",
            "address": {"address_line_1": "43 Commercial Road", "address_line_2": "The place", "country": "GB"},
        }
        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        site = self.organisation.primary_site
        site.refresh_from_db()

        self.assertEqual(site.name, data["name"])
        self.assertEqual(site.address.address_line_1, data["address"]["address_line_1"])
        self.assertEqual(site.address.address_line_2, data["address"]["address_line_2"])
        self.assertEqual(site.address.country, get_country(data["address"]["country"]))

    def test_cannot_add_site_without_permission(self):
        number_of_initial_sites = Site.objects.count()
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {}
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Site.objects.count(), number_of_initial_sites)

    def test_view_site(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        url = reverse(
            "organisations:site", kwargs={"org_pk": self.organisation.id, "site_pk": self.organisation.primary_site_id}
        )

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["site"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], self.organisation.primary_site.name)
        self.assertEqual(len(response_data["users"]), 1)

    def test_cannot_edit_site_without_permission(self):
        url = reverse(
            "organisations:site", kwargs={"org_pk": self.organisation.id, "site_pk": self.organisation.primary_site_id}
        )
        payload_name = "Not headquarters"
        data = {"name": payload_name}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(self.organisation.primary_site.name, payload_name)
