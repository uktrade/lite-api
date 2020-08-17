from django.urls import reverse
from rest_framework import status

from api.conf.constants import GovPermissions
from api.organisations.enums import OrganisationStatus
from api.organisations.tests.factories import OrganisationFactory
from test_helpers.clients import DataTestClient


class OrganisationTests(DataTestClient):
    url = reverse("gov_users:notifications")

    def test_get_notifications_with_in_review_organisations(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])
        OrganisationFactory(status=OrganisationStatus.IN_REVIEW)

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["notifications"], {"organisations": 1})
        self.assertEqual(response_data["has_notifications"], True)

    def test_get_notifications_without_organisation_permission(self):
        OrganisationFactory(status=OrganisationStatus.IN_REVIEW)

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["notifications"], {"organisations": 0})
        self.assertEqual(response_data["has_notifications"], False)

    def test_get_notifications_without_organisations(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["notifications"], {"organisations": 0})
        self.assertEqual(response_data["has_notifications"], False)
