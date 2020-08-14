from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from addresses.tests.factories import AddressFactory
from api.organisations.enums import OrganisationStatus
from api.organisations.tests.factories import OrganisationFactory, SiteFactory
from test_helpers.clients import DataTestClient


class MatchingOrganisationsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory(
            name="abc",
            status=OrganisationStatus.IN_REVIEW,
            eori_number="123",
            registration_number="123",
            primary_site=SiteFactory(address=AddressFactory(address_line_1="abc", address="abc")),
        )
        self.url = reverse("organisations:organisation_matching_details", kwargs={"pk": self.organisation.pk})

    def test_get_matching_organisations_no_organisations(self):
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()["matching_properties"])

    @parameterized.expand(
        [
            ({"name": "abc"}, "Name"),
            ({"eori_number": "123"}, "EORI Number"),
            ({"registration_number": "123"}, "Registration Number"),
        ]
    )
    def test_get_matching_organisation(self, org_details, expected_match):
        OrganisationFactory(**org_details)

        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["matching_properties"], [expected_match])

    def test_get_matching_organisation_uk_address(self):
        OrganisationFactory(primary_site=SiteFactory(address=AddressFactory(address_line_1="abc")),)

        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["matching_properties"], ["Address"])

    def test_get_matching_organisation_non_uk_address(self):
        OrganisationFactory(primary_site=SiteFactory(address=AddressFactory(address="abc")),)

        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["matching_properties"], ["Address"])
