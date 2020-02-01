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

    def test_get_existing_parties_only_returns_parties_from_own_organisation_success(self):
        second_organisation, _ = self.create_organisation_with_exporter_user(name="Second organisation")

        party = Party.objects.create(
            name="Mr Original",
            address="123 abc st.",
            website="https://www.gov.py",
            country=self.country,
            sub_type="government",
            organisation=second_organisation,
            type=PartyType.END_USER
        )

        response_data = self.client.get(self.url, **self.exporter_headers).data["results"]
        response_data_ids = [party["id"] for party in response_data]

        self.assertEqual(Party.objects.filter(organisation=self.organisation).count(), len(response_data))
        self.assertNotIn(str(party.id), response_data_ids)

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

    def test_get_existing_parties_contains_no_duplicates_without_filters_success(self):
        original_party = Party.objects.create(
            name="Mr Original",
            address="123 abc st.",
            website="https://www.gov.py",
            country=self.country,
            sub_type="government",
            organisation=self.organisation,
            type=PartyType.END_USER,
        )

        parties = [
            {"name": "Mr Original", "address": "456 abc st.", "website": "https://www.gov.py"},
            {"name": "Mr Copy", "address": "456 abc st.", "website": "https://www.gov.py"},
        ]

        for party in parties:
            Party.objects.create(
                **party,
                country=self.country,
                sub_type="government",
                organisation=self.organisation,
                copy_of_id=original_party.id,
                type=PartyType.END_USER
            )

        response_data = self.client.get(self.url, **self.exporter_headers).data["results"]

        response_data_ids = [party["id"] for party in response_data]
        expected_copy_id = Party.objects.filter(name="Mr Original", address="456 abc st.").get().id
        second_expected_copy_id = Party.objects.filter(name="Mr Copy").get().id

        # Party table data contains one duplicate, so results returned is 1 less than all parties
        self.assertEqual(Party.objects.count() - 1, len(response_data))

        self.assertIn(str(expected_copy_id), response_data_ids)
        self.assertIn(str(second_expected_copy_id), response_data_ids)
        self.assertIn(str(self.draft.end_user.party.id), response_data_ids)
        self.assertNotIn(str(original_party.id), response_data_ids)

    def test_get_existing_parties_contains_no_duplicates_with_filters_success(self):
        params = f"?name=Mr"

        original_party = Party.objects.create(
            name="Mr Original",
            address="123 abc st.",
            website="https://www.gov.py",
            country=self.country,
            sub_type="government",
            organisation=self.organisation,
            type=PartyType.END_USER
        )

        copied_party = Party.objects.create(
            name="Mr Original",
            address="123 abc st.",
            website="https://www.gov.py",
            country=self.country,
            sub_type="government",
            organisation=self.organisation,
            copy_of_id=original_party.id,
            type=PartyType.END_USER
        )

        response = self.client.get(self.url + params, **self.exporter_headers)
        response_data = response.data["results"]

        # Only expecting the most recent 'Mr' filter match
        self.assertEqual(1, len(response_data))
        self.assertEqual(str(copied_party.id), response_data[0]["id"])
