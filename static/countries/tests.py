import csv

from rest_framework import status
from rest_framework.reverse import reverse

from static.management.commands.seedcountries import COUNTRIES_FILE
from test_helpers.clients import DataTestClient


class CountriesTests(DataTestClient):

    url = reverse("static:countries:countries")

    def setUp(self):
        super().setUp()
        self.countries = None
        with open(COUNTRIES_FILE, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            # Convert CSV to a list of the names of the countries
            self.countries = [list(x.items())[0][1] for x in reader]

    def test_get_countries(self):
        response = self.client.get(self.url)
        countries = response.json()["countries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(countries[0]["name"], self.countries[0])
        self.assertEqual(countries[-1]["name"], self.countries[-1])

    def test_filter_countries_by_exclude(self):
        response = self.client.get(self.url + "?exclude=GB&exclude=PL")
        countries = response.json()["countries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(countries[0]["name"], self.countries[0])
        self.assertEqual(countries[-1]["name"], self.countries[-1])
        self.assertNotIn("United Kingdom", str(countries))
        self.assertNotIn("Poland", str(countries))
