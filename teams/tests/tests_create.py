from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from teams.models import Team
from test_helpers.clients import DataTestClient


class TeamCreateTests(DataTestClient):

    url = reverse('teams:teams')

    def tests_create_team(self):
        data = {
            'name': 'new team'
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.get().name, 'new team')

    @parameterized.expand([
        [{
            'name': 'this is a name'
        }],
        [{
            'name': 'ThIs iS A NaMe'
        }],
        [{
            'name': ' this is a name    '
        }],
    ])
    def tests_team_name_must_be_unique(self, data):
        Team(name='this is a name').save()
        response = self.client.post(self.url, data)
        self.assertEqual(Team.objects.all().count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

