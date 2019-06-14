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
        self.assertEqual(Team.objects.filter(name='new team').count(), 1)

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
        # Note: there already exists a team (Reception) which is created by default
        existing_teams_count = Team.objects.all().count()
        Team(name='this is a name').save()
        response = self.client.post(self.url, data)
        self.assertEqual(Team.objects.all().count(), existing_teams_count + 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

