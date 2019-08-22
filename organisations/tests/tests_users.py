from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class OrganisationUsersTests(DataTestClient):

    def test_view_all_users_belonging_to_organisation(self):
        """
        Ensure that the sole user of a newly created organisation can see themselves
        in the endpoint
        """
        url = reverse('organisations:users', kwargs={'org_pk': self.organisation.id})

        # Create an additional organisation and user to ensure
        # that only users from the first organisation are shown
        self.create_organisation('New Org')

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['users']), 1)
