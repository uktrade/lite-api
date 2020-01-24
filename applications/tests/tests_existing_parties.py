from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from parties.enums import PartyType
from parties.models import Party
from static.countries.models import Country
from test_helpers.clients import DataTestClient


class GetExistingPartiesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)
        self.url = reverse("applications:existing_parties", kwargs={"pk": self.draft.id})
        self.country = Country.objects.first()
        self.parties = [
            {"name": "Abc", "address": "123 abc st.", "website": "https://www.gov.py"},
            {"name": "Abc", "address": "456 abc st.", "website": "https://www.gov.py"},
        ]
        for party in self.parties:
            Party.objects.create(
                **party,
                type=PartyType.END_USER,
                country=self.country,
                sub_type="government",
                organisation=self.organisation,
            )

    def test_get_existing_parties(self):
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), Party.objects.count())

    @parameterized.expand(
        [("name", "Abc", 2), ("name", "blah", 0), ("address", "123 abc st.", 1), ("address", "456 abc st.", 1),]
    )
    def test_get_existing_parties_with_filters(self, key, value, expected_results):
        params = f"?{key}={value}"
        response = self.client.get(self.url + params, **self.exporter_headers)
        results = response.data["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for result in results:
            self.assertEqual(result[key], value)
        self.assertEqual(len(results), expected_results)

    def test_get_existing_parties_with_country_filter(self):
        params = f"?country={self.country.name}"
        response = self.client.get(self.url + params, **self.exporter_headers)
        results = response.data["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for result in results:
            self.assertEqual(result["country"]["id"], self.country.id)
        self.assertEqual(len(results), 2)

    def test_get_existing_party_with_all_filters(self):
        params = f"?name=Abc&address=123 abc st.&country={self.country.name}"
        response = self.client.get(self.url + params, **self.exporter_headers)
        results = response.data["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Abc")
        self.assertEqual(results[0]["address"], "123 abc st.")
        self.assertEqual(results[0]["country"]["id"], self.country.id)
