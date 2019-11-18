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
