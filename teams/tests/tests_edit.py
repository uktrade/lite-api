from django.urls import reverse
from rest_framework import status

from api.conf.constants import Teams
from teams.helpers import get_team_by_pk
from teams.models import Team
from test_helpers.clients import DataTestClient


class TeamEditTests(DataTestClient):
    def test_edit_team_name_successful(self):
        """
        Test that a valid gov user can edit their team name
        """
        team = Team(name="Team")
        team.save()

        data = {"name": "Renamed Team"}

        url = reverse("teams:team", kwargs={"pk": team.id})
        response = self.client.put(url, data, **self.gov_headers)

        team.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(team.name, data["name"])

    def test_cannot_rename_to_an_already_used_name_case_insensitive(self):
        """
        Test that a valid gov user cannot edit their team name
        to the same as another teams
        """
        team = Team(name="name")
        team.save()

        Team(name="test").save()

        data = {"name": "TEST"}

        url = reverse("teams:team", kwargs={"pk": team.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(team.name, data["name"])

    def test_cannot_edit_admin_team(self):
        team = get_team_by_pk(pk=Teams.ADMIN_TEAM_ID)

        data = {"name": "Renamed Team"}

        url = reverse("teams:team", kwargs={"pk": team.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(team.name, data["name"])
