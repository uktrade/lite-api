import json

from django.urls import path, include, reverse
from rest_framework import status

from teams.models import Team
from test_helpers.clients import DataTestClient


class GovUserEditTests(DataTestClient):

    urlpatterns = [
        path('gov-users/', include('gov_users.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    def setUp(self):
        super().setUp()

    def test_edit_a_gov_user(self):
        team = Team(name='Second')
        team.save()
        data = {
            'first_name': 'hamster',
            'last_name': 'gerbal',
            'email': 'some@thing.com',
            'team': team.id
        }

        url = reverse('gov_users:gov_user', kwargs={'pk': self.user.id})
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)

        self.assertNotEqual(response_data['gov_user']['first_name'], 'John')
        self.assertNotEqual(response_data['gov_user']['last_name'], 'Smith')
        self.assertNotEqual(response_data['gov_user']['email'], 'test@mail.com')
        self.assertNotEqual(response_data['gov_user']['team'], self.team)

        # Show that old email is no longer whitelisted
        url = reverse('gov_users:authenticate')
        data = {
            'email': 'test@mail.com',
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

