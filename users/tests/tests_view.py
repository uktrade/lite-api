from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from users.libraries.get_user import get_user_organisation_relationship


class UserTests(DataTestClient):

    url = reverse("users:me")

    def test_user_can_view_their_own_profile_info(self):
        """
        Tests the 'users/me' endpoint
        Ensures that the endpoint returns the correct details about the signed in user
        """
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.exporter_user.id))
        self.assertEqual(response_data["first_name"], self.exporter_user.first_name)
        self.assertEqual(response_data["last_name"], self.exporter_user.last_name)

    def test_retrieve_sites_that_a_user_belongs_to(self):
        """
        Ensure that the sites that a user is assigned to is returned when viewing their information
        """
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user, self.organisation)
        user_organisation_relationship.sites.set([self.organisation.primary_site])

        response = self.client.get(self.url, **self.exporter_headers)
        site = response.json()["sites"][0]

        self.assertEquals(
            site["id"], str(self.organisation.primary_site.id),
        )
        self.assertEquals(
            site["name"], str(self.organisation.primary_site.name),
        )
