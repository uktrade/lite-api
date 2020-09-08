from django.urls import reverse
from rest_framework import status

from api.core import constants
from api.users.tests.factories import GovUserFactory
from lite_content.lite_api import strings
from api.teams.models import Team
from test_helpers.clients import DataTestClient
from api.users.models import Role, GovUser


class GovUserEditTests(DataTestClient):
    def test_edit_a_gov_user(self):
        team = Team(name="Second")
        team.save()
        data = {"first_name": "hamster", "last_name": "gerbal", "email": "some@thing.com", "team": team.id}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.gov_user.pk})

        response = self.client.put(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response_data["gov_user"]["first_name"], "John")
        self.assertNotEqual(response_data["gov_user"]["last_name"], "Smith")
        self.assertNotEqual(response_data["gov_user"]["email"], "test@mail.com")
        self.assertNotEqual(response_data["gov_user"]["team"], self.team)

    def test_edit_gov_user_default_queue(self):
        original_default_queue = self.gov_user.default_queue
        data = {"default_queue": str(self.queue.id)}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.gov_user.pk})

        response = self.client.put(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response_data["gov_user"]["default_queue"], str(original_default_queue))
        self.assertEqual(response_data["gov_user"]["default_queue"], data["default_queue"])

    def test_edit_gov_user_invalid_default_queue(self):
        data = {"default_queue": "10000000-0000-0000-0000-000000000000"}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.gov_user.pk})

        response = self.client.put(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data["errors"]["default_queue"], [strings.Users.NULL_DEFAULT_QUEUE])

    def test_edit_gov_user_default_queue_with_non_related_team(self):
        new_team = self.create_team("new team")

        data = {"default_queue": str(self.queue.id), "team": str(new_team.id)}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.gov_user.pk})

        response = self.client.put(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["errors"]["default_queue"], [strings.Users.INVALID_DEFAULT_QUEUE % new_team.name]
        )

    def test_change_role_of_a_gov_user(self):
        self.gov_user.role = self.default_role
        self.gov_user.save()

        # create a second user to adopt the super user role as it will overwrite the save during the edit of the first user
        valid_user = GovUserFactory(
            baseuser_ptr__email="test2@mail.com",
            baseuser_ptr__first_name="John",
            baseuser_ptr__last_name="Smith",
            team=self.team)
        valid_user.save()

        role = Role(name="some role")
        role.permissions.set([constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        role.save()
        data = {"role": role.id}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.gov_user.pk})

        response = self.client.put(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["gov_user"]["role"], str(role.id))
