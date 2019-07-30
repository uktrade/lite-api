from django.urls import reverse
from rest_framework import status

from gov_users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class UserTests(DataTestClient):

    def test_only_get_users_belonging_to_my_organisation(self):
        """
        Tests the 'users/users' endpoint
        Ensures that a user can only see other users that belong to their organisation
        """
        url = reverse('users:users')

        # Add test data for another organisation
        test_helper_2 = OrgAndUserHelper(name='banana')
        organisation_2 = test_helper_2.organisation
        OrgAndUserHelper.create_additional_users(organisation_2, 4)

        response, status_code = self.get(url, **self.exporter_headers)

        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(len(response['users']), 1)

    def test_user_can_view_their_own_profile_info(self):
        """
        Tests the 'users/me' endpoint
        Ensures that the endpoint returns the correct details about the signed in user
        """
        url = reverse('users:me')

        response, status_code = self.get(url, **self.exporter_headers)

        self.assertEqual(status_code, status.HTTP_200_OK)

        self.assertEqual(response['user']['id'], str(self.exporter_user.id))
        self.assertEqual(response['user']['first_name'], self.exporter_user.first_name)
        self.assertEqual(response['user']['last_name'], self.exporter_user.last_name)

        self.assertEqual(response['user']['organisation']['id'], str(self.exporter_user.organisation.id))
        self.assertEqual(response['user']['organisation']['name'], self.exporter_user.organisation.name)
