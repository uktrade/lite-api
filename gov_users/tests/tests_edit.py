from django.urls import reverse
from rest_framework import status

from teams.models import Team
from test_helpers.clients import DataTestClient
from users.models import Role


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
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response_data['gov_user']['first_name'], 'John')
        self.assertNotEqual(response_data['gov_user']['last_name'], 'Smith')
        self.assertNotEqual(response_data['gov_user']['email'], 'test@mail.com')
        self.assertNotEqual(response_data['gov_user']['team'], self.team)

    def test_change_role_of_a_gov_user(self):
        role = Role(name='some role')
        role.save()
        data = {
            'role': role.id
        }
        url = reverse('gov_users:gov_user', kwargs={'pk': self.gov_user.id})

        response = self.client.put(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['gov_user']['role'], str(role.id))

