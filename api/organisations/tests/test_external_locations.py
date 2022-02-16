from rest_framework import status
from rest_framework.reverse import reverse

from lite_content.lite_api import strings
from api.organisations.enums import LocationType
from api.organisations.models import ExternalLocation
from test_helpers.clients import DataTestClient


class OrganisationExternalLocationsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.external_location = self.create_external_location(name="storage facility", org=self.organisation)
        self.url = reverse("organisations:external_locations", kwargs={"org_pk": self.organisation.pk})

    def test_site_list(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["external_locations"][0]["name"], self.external_location.name)

    def test_create_external_location(self):
        data = {"name": "regional site", "address": "A location", "country": "GB"}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExternalLocation.objects.all().count(), 2)

    def test_failed_create_external_location(self):
        data = {"name": "", "address": "", "country": ""}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExternalLocation.objects.all().count(), 1)

    def test_failed_create_land_based_sicl_external_location(self):
        """
        Land based external locations will require a country
        """
        data = {
            "name": "regional site",
            "address": "123 Test",
            "country": "",
            "location_type": LocationType.LAND_BASED,
            "application_type": "sicl",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["country"][0],
            strings.Addresses.NULL_COUNTRY,
        )
        self.assertEqual(ExternalLocation.objects.all().count(), 1)

    def test_create_sea_based_sicl_external_location_without_country(self):
        """
        Sea based external locations will not require a country
        """
        data = {
            "name": "regional site",
            "address": "123 Test",
            "location_type": LocationType.SEA_BASED,
            "application_type": "sicl",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["external_location"]["name"], "regional site")
        self.assertEqual(response.json()["external_location"]["address"], "123 Test")
        self.assertEqual(response.json()["external_location"]["location_type"], LocationType.SEA_BASED)
        self.assertEqual(response.json()["external_location"]["country"], None)
        self.assertEqual(ExternalLocation.objects.all().count(), 2)

    def test_failed_create_sicl_external_location_without_location_type(self):
        """
        SICL external locations require a location_type
        """
        data = {
            "name": "regional site",
            "address": "123 Test",
            "country": "FR",
            "location_type": "",
            "application_type": "sicl",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["location_type"][0],
            strings.ExternalLocations.Errors.LOCATION_TYPE,
        )
        self.assertEqual(ExternalLocation.objects.all().count(), 1)
