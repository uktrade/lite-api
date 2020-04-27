from django.urls import reverse
from rest_framework import status

from teams.models import Team
from teams.tests.factories import TeamFactory
from test_helpers.clients import DataTestClient


class TeamListTests(DataTestClient):

    url = reverse("teams:teams")

    def test_team_list(self):
        existing_teams_count = Team.objects.all().count()
        TeamFactory()
        TeamFactory()
        TeamFactory()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["teams"]), existing_teams_count + 3)
