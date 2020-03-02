import csv

from rest_framework import status
from rest_framework.reverse import reverse

from static.countries.models import Country
from test_helpers.clients import DataTestClient


class CountriesTests(DataTestClient):

    url = reverse("static:countries:countries")

    def setUp(self):
        super().setUp()

    def test_get_countries(self):
        response = self.client.get(self.url)
        countries = response.json()["countries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Country.objects.filter(name=countries[0]["name"]).exists())
        self.assertTrue(Country.objects.filter(name=countries[-1]["name"]).exists())

    def test_filter_countries_by_exclude(self):
        response = self.client.get(self.url + "?exclude=GB&exclude=PL")
        countries = response.json()["countries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Country.objects.filter(name=countries[0]["name"]).exists())
        self.assertTrue(Country.objects.filter(name=countries[-1]["name"]).exists())
        self.assertNotIn("United Kingdom", str(countries))
        self.assertNotIn("Poland", str(countries))
