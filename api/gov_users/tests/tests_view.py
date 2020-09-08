from django.urls import reverse
from rest_framework import status

from api.gov_users.enums import GovUserStatuses
from api.users.tests.factories import GovUserFactory
from test_helpers.clients import DataTestClient
from api.users.enums import UserStatuses
from api.users.models import GovUser


class GovUserViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.team_1 = self.create_team("Team 1")
        self.user_1 = GovUserFactory(
            baseuser_ptr__email="test1@mail.com",
            baseuser_ptr__first_name="Jane",
            baseuser_ptr__last_name="Smith",
            team=self.team_1,
            status=UserStatuses.DEACTIVATED
        )

        self.team_2 = self.create_team("Team 2")
        self.user_2 = GovUserFactory(
            baseuser_ptr__email="test2@mail.com",
            baseuser_ptr__first_name="John",
            baseuser_ptr__last_name="Smith",
            team=self.team_2,
            status=UserStatuses.ACTIVE,
        )

        self.users = [self.user_1, self.user_2]

    def test_get_gov_users(self):
        response = self.client.get(reverse("gov_users:gov_users"), **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), GovUser.objects.all().count())
        for user in self.users:
            self.assertTrue(str(user.pk) in [user["id"] for user in response_data])
            self.assertTrue(user.email in [user["email"] for user in response_data])

    def test_get_individual_gov_user(self):
        user = self.user_1

        response = self.client.get(reverse("gov_users:gov_user", kwargs={"pk": user.pk}), **self.gov_headers)
        response_data = response.json()["user"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(user.pk), response_data["id"])
        self.assertEqual(user.email, response_data["email"])
        self.assertEqual(user.first_name, response_data["first_name"])
        self.assertEqual(user.last_name, response_data["last_name"])
        self.assertEqual(str(user.team.id), response_data["team"]["id"])

    def test_filter_users_by_team(self):
        response = self.client.get(reverse("gov_users:gov_users") + "?teams=" + str(self.team_1.id), **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(str(self.user_1.pk), response_data[0]["id"])
        self.assertEqual(self.user_1.email, response_data[0]["email"])

    def test_filter_users_by_multiple_teams(self):
        response = self.client.get(
            reverse("gov_users:gov_users") + "?teams=" + str(self.team_1.id) + "," + str(self.team_2.id),
            **self.gov_headers,
        )
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 2)
        for user in self.users:
            self.assertTrue(str(user.pk) in [user["id"] for user in response_data])
            self.assertTrue(user.email in [user["email"] for user in response_data])

    def test_filter_users_by_email(self):
        response = self.client.get(
            reverse("gov_users:gov_users") + "?email=" + self.gov_user.email, **self.gov_headers,
        )
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(str(self.gov_user.pk) in [user["id"] for user in response_data])
        self.assertTrue(self.gov_user.email in [user["email"] for user in response_data])

    def test_get_all_user_statuses(self):
        response = self.client.get(reverse("gov_users:gov_users") + f"?status=", **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), GovUser.objects.all().count())

    def test_get_active_users(self):
        url = reverse("gov_users:gov_users") + "?status=" + GovUserStatuses.ACTIVE
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]
        ids = [user["id"] for user in response_data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), GovUser.objects.filter(status=UserStatuses.ACTIVE).count())
        self.assertTrue(str(self.user_2.pk) in ids)
        self.assertFalse(str(self.user_1.pk) in ids)

    def test_get_deactivated_users(self):
        url = reverse("gov_users:gov_users") + "?status=" + GovUserStatuses.DEACTIVATED
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]
        ids = [user["id"] for user in response_data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), GovUser.objects.filter(status=UserStatuses.DEACTIVATED).count())
        self.assertFalse(str(self.user_2.pk) in ids)
        self.assertTrue(str(self.user_1.pk) in ids)
