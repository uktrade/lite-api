from django.urls import reverse
from rest_framework import status

from teams.models import Team
from test_helpers.clients import DataTestClient
from users.models import Permission, Role


class GovUserEditTests(DataTestClient):

    def test_edit_a_gov_user(self):
        team = Team(name='Second')
        team.save()
        data = {
            'first_name': 'hamster',
            'last_name': 'gerbal',
            'email': 'some@thing.com',
            'team': team.id
        }

        url = reverse('gov_users:gov_user', kwargs={'pk': self.gov_user.id})
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertNotEqual(response_data['gov_user']['first_name'], 'John')
        self.assertNotEqual(response_data['gov_user']['last_name'], 'Smith')
        self.assertNotEqual(response_data['gov_user']['email'], 'test@mail.com')
        self.assertNotEqual(response_data['gov_user']['team'], self.team)

        # Show that old email is no longer whitelisted
        url = reverse('gov_users:authenticate')
        data = {
            'email': 'test@mail.com',
            'first_name': self.gov_user.first_name,
            'last_name': self.gov_user.last_name
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tests_change_role_of_a_gov_user(self):
        role = Role(name='some role')
        role.permissions.set([Permission.objects.get(name='Manage final advice').id])
        role.save()
        data = {
            'role': role.id
        }
        url = reverse('gov_users:gov_user', kwargs={'pk': self.gov_user.id})
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data['gov_user']['role'], str(role.id))

