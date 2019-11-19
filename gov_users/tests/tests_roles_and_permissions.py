from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from conf.constants import Permissions, Roles
from test_helpers.clients import DataTestClient
from users.models import Role, Permission


class RolesAndPermissionsTests(DataTestClient):

    url = reverse("gov_users:roles_views")

    def test_create_new_role_with_permission_to_make_final_decisions(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        data = {
            "name": "some role",
            "permissions": [Permissions.MANAGE_FINAL_ADVICE],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name="some role").name, "some role")

    def test_create_new_role_with_no_permissions(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        data = {
            "name": "some role",
            "permissions": [],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name="some role").name, "some role")

    def test_get_list_of_all_roles_as_non_super_user(self):
        role = Role(name="some")
        role.permissions.set([Permissions.MANAGE_FINAL_ADVICE])
        role.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["roles"]), 2)

    def test_get_list_of_all_roles_as_super_user(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        role = Role(name="some")
        initial_roles_count = Role.objects.count()
        role.permissions.set([Permissions.MANAGE_FINAL_ADVICE])
        role.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["roles"]), initial_roles_count + 1)

    def test_get_list_of_all_permissions(self):
        url = reverse("gov_users:permissions")

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["permissions"]), Permission.objects.count())

    def test_edit_a_role(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        role_id = Roles.DEFAULT_ROLE_ID
        url = reverse("gov_users:role", kwargs={"pk": role_id})

        data = {"permissions": [Permissions.MANAGE_FINAL_ADVICE]}

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Permissions.MANAGE_FINAL_ADVICE in Role.objects.get(id=role_id).permissions.values_list("id", flat=True)
        )

    @parameterized.expand(
        [
            [{"name": "this is a name", "permissions": []}],
            [{"name": "ThIs iS A NaMe", "permissions": []}],
            [{"name": " this is a name    ", "permissions": []}],
        ]
    )
    def test_role_name_must_be_unique(self, data):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        initial_roles_count = Role.objects.count()
        Role(name="this is a name").save()

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(Role.objects.all().count(), initial_roles_count + 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_role_without_permission(self):
        data = {
            "name": "some role",
            "permissions": [],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_edit_role_without_permission(self):
        role_id = Roles.DEFAULT_ROLE_ID
        url = reverse("gov_users:role", kwargs={"pk": role_id})

        data = {"permissions": [Permissions.MANAGE_FINAL_ADVICE]}

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_edit_a_role_add_confirm_own_advice_adds_manage_team_advice(self):
        role = Role(name="New Role")
        role.permissions.set([Permissions.ADMINISTER_ROLES])
        role.save()
        role_id = role.id
        self.gov_user.role = role
        self.gov_user.save()
        url = reverse("gov_users:role", kwargs={"pk": role_id})
        data = {"permissions": [Permissions.CONFIRM_OWN_ADVICE]}

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Permissions.CONFIRM_OWN_ADVICE in Role.objects.get(id=role_id).permissions.values_list("id", flat=True)
        )
        self.assertTrue(
            Permissions.MANAGE_TEAM_ADVICE in Role.objects.get(id=role_id).permissions.values_list("id", flat=True)
        )

    def test_edit_a_role_remove_manage_team_advice_removes_confirm_own_advice(self):
        role = Role(name="New Role")
        role.permissions.set(
            [Permissions.ADMINISTER_ROLES, Permissions.MANAGE_TEAM_ADVICE, Permissions.CONFIRM_OWN_ADVICE]
        )
        role.save()
        role_id = role.id
        self.gov_user.role = role
        self.gov_user.save()
        url = reverse("gov_users:role", kwargs={"pk": role_id})
        data = {"permissions": [Permissions.CONFIRM_OWN_ADVICE]}

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Permissions.CONFIRM_OWN_ADVICE not in Role.objects.get(id=role_id).permissions.values_list("id", flat=True)
        )
        self.assertTrue(
            Permissions.MANAGE_TEAM_ADVICE not in Role.objects.get(id=role_id).permissions.values_list("id", flat=True)
        )
