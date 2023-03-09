from django.urls import reverse
from rest_framework import status
from urllib import parse

from test_helpers.clients import DataTestClient


class DataWorkspaceApplicationViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        test_host = "http://testserver"
        self.users_base_users = parse.urljoin(test_host, reverse("data_workspace:dw-users-base-users-list"))
        self.users_gov_users = parse.urljoin(test_host, reverse("data_workspace:dw-users-gov-users-list"))

    def test_dw_users_base_users(self):
        response = self.client.options(self.users_base_users)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["actions"]["GET"].keys()
        expected_keys = {
            "id",
            "created_at",
            "updated_at",
            "first_name",
            "last_name",
            "date_joined",
            "email",
            "type",
            "phone_number",
            "pending",
            "groups",
            "user_permissions",
        }
        self.assertEqual(expected_keys, actual_keys)

    def test_dw_users_gov_users(self):
        response = self.client.options(self.users_gov_users)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_keys = {
            "id",
            "first_name",
            "last_name",
            "email",
            "status",
            "team",
            "role",
            "default_queue",
        }
        actual_keys = response.json()["actions"]["GET"].keys()
        self.assertEqual(expected_keys, actual_keys)
