from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from users.enums import UserStatuses
from users.models import GovUser


class GovUserViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user_preexisting_count = GovUser.objects.all().count()
        self.team_2 = self.create_team("Team 2")
        self.user = GovUser(email="test2@mail.com", first_name="John", last_name="Smith", team=self.team_2)
        self.user.save()

    def test_get_individual_gov_user(self):
        response = self.client.get(reverse("gov_users:gov_users"), **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["gov_users"]), self.gov_user_preexisting_count + 1)

    def test_filter_users(self):
        response = self.client.get(reverse("gov_users:gov_users") + "?teams=" + str(self.team.id), **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["gov_users"]), self.gov_user_preexisting_count)

    def test_filter_users_by_multiple_teams(self):
        response = self.client.get(
            reverse("gov_users:gov_users") + "?teams=" + str(self.team.id) + "," + str(self.team_2.id),
            **self.gov_headers,
        )
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["gov_users"]), self.gov_user_preexisting_count + 1)

    def test_dont_get_deactivated_users(self):
        self.user.status = UserStatuses.DEACTIVATED
        self.user.save()

        self.url = reverse("gov_users:gov_users") + "?activated=True"

        response = self.client.get(self.url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response_data["gov_users"]), self.gov_user_preexisting_count)
