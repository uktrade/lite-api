from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient
from users.enums import UserStatuses
from users.libraries.get_user import get_users_from_organisation
from users.models import UserOrganisationRelationship, ExporterUser


class OrganisationUsersTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.url = reverse('organisations:users', kwargs={'org_pk': self.organisation.id})

    def test_view_all_users_belonging_to_organisation(self):
        """
        Ensure that the sole user of a newly created organisation can see themselves
        in the endpoint
        """
        # Create an additional organisation and user to ensure
        # that only users from the first organisation are shown
        self.create_organisation('New Org')

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()['users']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['status'], UserStatuses.ACTIVE)

    def test_add_user_to_organisation_success(self):
        """
        Ensure that a user can be added to an organisation
        """
        data = {
            'first_name': 'Matt',
            'last_name': 'Berninger',
            'email': 'matt.berninger@americanmary.com',
        }

        ExporterUser(first_name=data['first_name'],
                     last_name=data['last_name'],
                     email=data['email']).save()

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(len(UserOrganisationRelationship.objects.all()), 2)

    def test_add_existing_user_to_organisation_failure(self):
        """
        Ensure that a user cannot be added twice to the
        same organisation
        """
        data = {
            'first_name': self.exporter_user.first_name,
            'last_name': self.exporter_user.last_name,
            'email': self.exporter_user.email,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is already a member of this organisation.', response_data['errors']['email'][0])
        self.assertTrue(len(UserOrganisationRelationship.objects.all()), 1)

    def test_add_user_to_another_organisation_success(self):
        """
        Ensure that a user can be added to multiple organisations
        """
        organisation_2 = self.create_organisation()
        user = get_users_from_organisation(organisation_2)[0]

        data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(len(get_users_from_organisation(self.organisation)), 2)
