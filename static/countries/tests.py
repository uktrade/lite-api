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
        self.assertEqual(Country.objects.count(), len(countries))
        self.assertTrue(Country.objects.filter(name=countries[0]["name"]).exists())
        self.assertTrue(Country.objects.filter(name=countries[-1]["name"]).exists())

    def test_filter_countries_by_exclude(self):
        country_one = Country.objects.first()
        country_two = Country.objects.last()

        response = self.client.get(self.url + f"?exclude={country_one.id}&exclude={country_two.id}")
        countries = response.json()["countries"]
        country_names = [country["name"] for country in countries]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Country.objects.count() - 2, len(countries))
        self.assertNotIn(country_one.name, country_names)
        self.assertNotIn(country_two.name, country_names)

