from django.urls import reverse
from rest_framework import status

from api.core.constants import Teams
from api.teams.helpers import get_team_by_pk
from api.teams.models import Team
from test_helpers.clients import DataTestClient


class TeamEditTests(DataTestClient):
    def test_edit_team_name_successful(self):
        """
        Test that a valid gov user can edit their team name
        """
        team = Team(name="Team", part_of_ecju=True)
        team.save()

        data = {"name": "Renamed Team", "part_of_ecju": False, "is_ogd": False}

        url = reverse("teams:team", kwargs={"pk": team.id})
        response = self.client.put(url, data, **self.gov_headers)

        team.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(team.name, data["name"])
        self.assertEqual(team.part_of_ecju, data["part_of_ecju"])
        self.assertEqual(team.part_of_ecju, data["is_ogd"])

    def test_edit_team_missing_part_of_ecju(self):
        team = Team(name="Team")
        team.save()

        data = {"name": "Renamed Team", "is_ogd": False}

        url = reverse("teams:team", kwargs={"pk": team.id})
        response = self.client.put(url, data, **self.gov_headers)
        team.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["part_of_ecju"][0], "Select yes if the team is part of ECJU")

    def test_edit_team_missing_is_ogd(self):
        team = Team(name="Team")
        team.save()

        data = {"name": "Renamed Team", "part_of_ecju": False}

        url = reverse("teams:team", kwargs={"pk": team.id})
        response = self.client.put(url, data, **self.gov_headers)
        team.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["is_ogd"][0], "Select yes if the team is an OGD")

    def test_cannot_rename_to_an_already_used_name_case_insensitive(self):
        """
        Test that a valid gov user cannot edit their team name
        to the same as another teams
        """
        team = Team(name="name", part_of_ecju=False, is_ogd=False)
        team.save()

        Team(name="test").save()

        data = {"name": "TEST"}

        url = reverse("teams:team", kwargs={"pk": team.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(team.name, data["name"])

    def test_cannot_edit_admin_team(self):
        team = get_team_by_pk(pk=Teams.ADMIN_TEAM_ID)

        data = {"name": "Renamed Team", "part_of_ecju": True, "is_ogd": False}

        url = reverse("teams:team", kwargs={"pk": team.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(team.name, data["name"])
