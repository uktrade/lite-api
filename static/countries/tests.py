from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class CountriesTests(DataTestClient):

    url = reverse("static:countries:countries")

    def test_get_countries(self):
        response = self.client.get(self.url)
        countries = response.json()["countries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(countries[0]["name"], "Abu Dhabi")
        self.assertEqual(countries[-1]["name"], "Zimbabwe")

    def test_filter_countries_by_exclude(self):
        response = self.client.get(self.url + "?exclude=GB&exclude=PL")
        countries = response.json()["countries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(countries[0]["name"], "Abu Dhabi")
        self.assertEqual(countries[-1]["name"], "Zimbabwe")
        self.assertNotIn("United Kingdom", str(countries))
        self.assertNotIn("Poland", str(countries))
