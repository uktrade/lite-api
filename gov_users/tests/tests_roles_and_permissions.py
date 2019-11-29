from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from conf.constants import Permissions, Roles
from test_helpers.clients import DataTestClient
from users.enums import UserType
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

    def test_get_list_of_all_roles_as_super_user(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        role = Role(name="some")
        role.permissions.set([Permissions.MANAGE_FINAL_ADVICE])
        role.save()
        initial_roles_count = Role.objects.filter(type=UserType.INTERNAL).count()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["roles"]), initial_roles_count)

    def test_edit_a_role(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        role_id = Roles.INTERNAL_DEFAULT_ROLE_ID
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
        Role(name="this is a name").save()
        initial_roles_count = Role.objects.count()

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Role.objects.all().count(), initial_roles_count)

    def test_cannot_create_role_without_permission(self):
        data = {
            "name": "some role",
            "permissions": [],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_edit_role_without_permission(self):
        role_id = Roles.INTERNAL_DEFAULT_ROLE_ID
        url = reverse("gov_users:role", kwargs={"pk": role_id})

        data = {"permissions": [Permissions.MANAGE_FINAL_ADVICE]}

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @parameterized.expand(
        [
            [[Permissions.MANAGE_TEAM_ADVICE, Permissions.MANAGE_FINAL_ADVICE, Permissions.REVIEW_GOODS]],
            [[Permissions.MANAGE_TEAM_ADVICE, Permissions.MANAGE_FINAL_ADVICE]],
            [[Permissions.MANAGE_TEAM_ADVICE]],
        ]
    )
    def test_only_see_roles_user_has_all_permissions_for(self, permissions):
        user_role = Role(name="new role")
        user_role.permissions.set(permissions)
        user_role.save()
        self.gov_user.role = user_role
        self.gov_user.save()

        i = 0
        # Create a new role, each with a singular different permission
        for permission in Permission.internal.all():
            role = Role(name="name: " + str(i))
            role.permissions.set([permission.id])
            role.save()
            i += 1
        second_role = Role(name="multi permission role")
        second_role.permissions.set(
            [Permissions.MANAGE_TEAM_ADVICE, Permissions.MANAGE_FINAL_ADVICE, Permissions.REVIEW_GOODS]
        )
        second_role.save()
        # Adjust expected result to cover the multi permission role
        r = 1 if len(permissions) == 3 else 0

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["roles"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(permissions) + 2 + r)

    @parameterized.expand(
        [
            [[Permissions.MANAGE_TEAM_ADVICE, Permissions.MANAGE_FINAL_ADVICE, Permissions.REVIEW_GOODS]],
            [[Permissions.MANAGE_TEAM_ADVICE, Permissions.MANAGE_FINAL_ADVICE]],
            [[Permissions.MANAGE_TEAM_ADVICE]],
        ]
    )
    def test_only_see_permissions_user_already_has(self, permissions):
        user_role = Role(name="new role")
        user_role.permissions.set(permissions)
        user_role.save()
        self.gov_user.role = user_role
        self.gov_user.save()
        url = reverse("gov_users:permissions")

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["permissions"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(permissions))
        for permission in permissions:
            self.assertIn(permission, [p["id"] for p in response_data])
