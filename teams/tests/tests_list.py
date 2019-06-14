from django.urls import reverse
from rest_framework import status

from teams.models import Team
from test_helpers.clients import DataTestClient


class TeamListTests(DataTestClient):

    url = reverse('teams:teams')

    def tests_team_list(self):
        # Note: there already exists a team (Reception) which is created by default
        existing_teams_count = Team.objects.all().count()
        Team(name='name 1').save()
        Team(name='name 2').save()
        Team(name='name 3').save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["teams"]), existing_teams_count + 3)
