import json

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

        test_helper_2 = OrgAndUserHelper(name='banana')
        organisation_2 = test_helper_2.organisation

        OrgAndUserHelper.create_additional_users(self.test_helper.organisation, 2)
        OrgAndUserHelper.create_additional_users(organisation_2, 4)

        response = self.client.get(url, **self.exporter_headers)
        response_data = json.loads(response.content)

        # Expect to see one more than the additional number of users created as there is one initial admin user
        self.assertEqual(len(response_data['users']), 3)

        response = self.client.get(url, **{'HTTP_EXPORTER_USER_TOKEN': user_to_token(test_helper_2.user)})
        response_data = json.loads(response.content)

        self.assertEqual(len(response_data['users']), 5)

    def test_user_can_view_their_own_profile_info(self):
        """
        Tests the 'users/me' endpoint
        Ensures that the endpoint returns the correct details about the signed in user
        """
        url = reverse('users:me')

        response = self.client.get(url, **self.exporter_headers)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response_data['user']['id'], str(self.exporter_user.id))
        self.assertEqual(response_data['user']['first_name'], str(self.exporter_user.first_name))
        self.assertEqual(response_data['user']['last_name'], str(self.exporter_user.last_name))

        self.assertEqual(response_data['user']['organisation']['id'], str(self.exporter_user.organisation.id))
        self.assertEqual(response_data['user']['organisation']['name'], str(self.exporter_user.organisation.name))
