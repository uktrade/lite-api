from django.urls import reverse
from rest_framework import status

from api.teams.models import Team
from api.users.tests.factories import GovUserFactory
from test_helpers.clients import DataTestClient
from api.users.models import GovUser


class UserByTeamListTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user_preexisting_count = GovUser.objects.all().count()
        self.team = self.gov_user.team

    def test_view_user_by_team(self):
        """
        Tests that a valid gov user can see a specific team's members
        """
        team2 = Team(name="Second")
        team2.save()

        GovUserFactory(
            baseuser_ptr__email="test2@mail.com",
            baseuser_ptr__first_name="John",
            baseuser_ptr__last_name="Smith",
            team=self.team,
        )
        GovUserFactory(
            baseuser_ptr__email="test3@mail.com",
            baseuser_ptr__first_name="John",
            baseuser_ptr__last_name="Smith",
            team=team2,
        )

        url = reverse("teams:team_users", kwargs={"pk": self.team.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["users"]), self.gov_user_preexisting_count)
        self.assertContains(response, "test2@mail.com")
        self.assertNotContains(response, "test3@mail.com")
