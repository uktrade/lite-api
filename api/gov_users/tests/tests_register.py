from django.urls import reverse
from rest_framework import status

from api.core.constants import Roles
from api.gov_users.enums import GovUserStatuses
from lite_content.lite_api import strings
from api.queues.constants import MY_TEAMS_QUEUES_CASES_ID
from test_helpers.clients import DataTestClient
from api.users.models import GovUser


class GovUserAuthenticateTests(DataTestClient):
    def test_user_registers_new_user(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jsmith@name.com",
            "team": self.team.id,
            "role": Roles.INTERNAL_DEFAULT_ROLE_ID,
            "default_queue": MY_TEAMS_QUEUES_CASES_ID,
        }

        url = reverse("gov_users:gov_users")
        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_user = GovUser.objects.get(email="jsmith@name.com")
        self.assertEqual(new_user.status, GovUserStatuses.ACTIVE)
        self.assertEqual(new_user.email, "jsmith@name.com")

    def test_create_new_user_failure(self):
        self.gov_user_preexisting_count = GovUser.objects.all().count()

        url = reverse("gov_users:gov_users")
        response = self.client.post(url, {}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GovUser.objects.all().count(), self.gov_user_preexisting_count)

    def test_super_user_can_create_new_super_user(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jsmith@name.com",
            "team": self.team.id,
            "role": Roles.INTERNAL_SUPER_USER_ROLE_ID,
            "default_queue": MY_TEAMS_QUEUES_CASES_ID,
        }

        url = reverse("gov_users:gov_users")
        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_super_user_cannot_create_new_super_user(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jsmith@name.com",
            "team": self.team.id,
            "role": Roles.INTERNAL_SUPER_USER_ROLE_ID,
            "default_queue": MY_TEAMS_QUEUES_CASES_ID,
        }

        url = reverse("gov_users:gov_users")
        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_gov_user_invalid_default_queue(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jsmith@name.com",
            "team": str(self.team.id),
            "role": Roles.INTERNAL_DEFAULT_ROLE_ID,
            "default_queue": "10000000-0000-0000-0000-000000000000",
        }

        url = reverse("gov_users:gov_users")
        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["errors"]["default_queue"], [strings.Users.NULL_DEFAULT_QUEUE])

    def test_create_gov_user_default_queue_with_non_related_team(self):
        new_team = self.create_team("new team")
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jsmith@name.com",
            "team": str(new_team.id),
            "role": Roles.INTERNAL_DEFAULT_ROLE_ID,
            "default_queue": str(self.queue.id),
        }

        url = reverse("gov_users:gov_users")
        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["errors"]["default_queue"], [strings.Users.INVALID_DEFAULT_QUEUE % new_team.name]
        )
