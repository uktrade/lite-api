from django.apps import apps

from rest_framework import status
from rest_framework.reverse import reverse
import pytest

from api.staticdata.countries.models import Country
from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class CountriesTests(DataTestClient):
    url = reverse("staticdata:countries:countries")

    def test_get_countries(self):
        response = self.client.get(self.url, **self.exporter_headers)
        countries = response.json()["countries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Country.exclude_special_countries.count(), len(countries))
        self.assertTrue(Country.exclude_special_countries.filter(name=countries[0]["name"]).exists())
        self.assertTrue(Country.exclude_special_countries.filter(name=countries[-1]["name"]).exists())

    def test_filter_countries_by_exclude(self):
        country_one = Country.objects.first()
        country_two = Country.objects.last()

        response = self.client.get(
            self.url + f"?exclude={country_one.id}&exclude={country_two.id}", **self.exporter_headers
        )
        countries = response.json()["countries"]
        country_names = [country["name"] for country in countries]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Country.exclude_special_countries.count() - 2, len(countries))
        self.assertNotIn(country_one.name, country_names)
        self.assertNotIn(country_two.name, country_names)

    def test_get_country(self):
        response = self.client.get(
            reverse("staticdata:countries:country", kwargs={"pk": "GB"}), **self.exporter_headers
        )
        response_data = response.json()
        country = Country.objects.get(pk="GB")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], country.pk)
        self.assertEqual(response_data["name"], country.name)
        self.assertEqual(response_data["type"], country.type)
        self.assertEqual(response_data["is_eu"], country.is_eu)


class CountriesResponseTests(EndPointTests):
    url = "/static/countries/"

    def test_countries(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)


@pytest.mark.django_db
def test_rename_countries_migration(migration):
    old_apps = migration.before([("countries", "0001_squashed_0003_auto_20210105_1058")])
    Country = apps.get_model("countries", "Country")
    assert Country.objects.filter(name="United Kingdom").first().name == "United Kingdom"
    # executing migration
    new_apps = migration.apply("countries", "0002_rename_countries")
    assert Country.objects.filter(name="Great Britain").first().name == "Great Britain"


@pytest.mark.django_db
def test_add_gb_nir(migration):
    old_apps = migration.before([("countries", "0002_rename_countries")])
    Country = apps.get_model("countries", "Country")
    Country.objects.create(id="GB", name="Great Britain", type="gov.uk Country", is_eu=True)
    assert Country.objects.filter(name="Northern Ireland").first() is None
    # executing migration
    new_apps = migration.apply("countries", "0003_add_nir")
    assert Country.objects.filter(name="Northern Ireland").exists() is True
    assert Country.objects.filter(name="Great Britain").first().is_eu is False
