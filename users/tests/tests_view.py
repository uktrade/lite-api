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
        response, status_code = self.get(self.url, **self.exporter_headers)

        self.assertEqual(status_code, status.HTTP_200_OK)

        self.assertEqual(response["user"]["id"], str(self.exporter_user.id))
        self.assertEqual(response["user"]["first_name"], self.exporter_user.first_name)
        self.assertEqual(response["user"]["last_name"], self.exporter_user.last_name)

    def test_retrieve_sites_that_a_user_belongs_to(self):
        """
        Ensure that the sites that a user is assigned to is returned when viewing their information
        """
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user, self.organisation)
        user_organisation_relationship.sites.set([self.organisation.primary_site])

        response, _ = self.get(self.url, **self.exporter_headers)
        site = response["user"]["sites"][0]

        self.assertEquals(
            site["id"], str(self.organisation.primary_site.id),
        )
        self.assertEquals(
            site["name"], str(self.organisation.primary_site.name),
        )
