from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.teams.models import Team
from test_helpers.clients import DataTestClient


class TeamCreateTests(DataTestClient):

    url = reverse("teams:teams")

    def setUp(self):
        super().setUp()
        self.team_preexisting_count = Team.objects.all().count()

    def test_create_team_missing_part_of_ecju(self):
        data = {"name": "new team", "is_ogd": False}
        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["part_of_ecju"][0], "Select yes if the team is part of ECJU")

    def test_create_team_missing_is_ogd(self):
        data = {"name": "new team", "part_of_ecju": False}
        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["is_ogd"][0], "Select yes if the team is an OGD")

    def test_create_team(self):
        data = {"name": "new team", "part_of_ecju": True, "is_ogd": True}
        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.filter(name="new team").count(), 1)
        self.assertEqual(Team.objects.get(name="new team").name, "new team")
        self.assertEqual(Team.objects.get(name="new team").part_of_ecju, True)
        self.assertEqual(Team.objects.get(name="new team").is_ogd, True)

    @parameterized.expand(
        [[{"name": "this is a name"}], [{"name": "ThIs iS A NaMe"}], [{"name": " this is a name    "}]]
    )
    def test_team_name_must_be_unique(self, data):
        Team(name="this is a name", part_of_ecju=True).save()

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(Team.objects.all().count(), self.team_preexisting_count + 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
