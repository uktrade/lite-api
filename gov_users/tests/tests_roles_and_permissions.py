from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.conf import constants
from api.conf.constants import Roles
from test_helpers.clients import DataTestClient
from api.users.enums import UserType
from api.users.models import Role, Permission


class RolesAndPermissionsTests(DataTestClient):

    url = reverse("gov_users:roles_views")

    def test_create_new_role_with_permission_to_make_final_decisions(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        data = {"name": "some role", "permissions": [constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name]}

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name="some role").name, "some role")

    def test_create_new_role_with_no_permissions(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        data = {"name": "some role", "permissions": []}

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name="some role").name, "some role")

    def test_get_list_of_all_roles_as_super_user(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        role = Role(name="some")
        role.permissions.set([constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
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

        data = {"permissions": [constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name]}

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name
            in Role.objects.get(id=role_id).permissions.values_list("id", flat=True)
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
        data = {"name": "some role", "permissions": []}

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_edit_role_without_permission(self):
        role_id = Roles.INTERNAL_DEFAULT_ROLE_ID
        url = reverse("gov_users:role", kwargs={"pk": role_id})

        data = {"permissions": [constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name]}

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_roles_that_a_user_sees_are_roles_with_a_subset_of_the_permissions_of_the_users_own_role_max(self):
        permissions = [
            constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
            constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
            constants.GovPermissions.REVIEW_GOODS.name,
        ]
        user_role = Role(name="new role")
        user_role.permissions.set(permissions)
        user_role.save()
        self.gov_user.role = user_role
        self.gov_user.save()

        # Create a new role, each with a singular different permission
        for permission in Permission.internal.all():
            role = Role(name=str(permission.id))
            role.permissions.set([permission.id])
            role.save()
        second_role = Role(name="multi permission role")
        second_role.permissions.set(
            [
                constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
                constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
                constants.GovPermissions.REVIEW_GOODS.name,
            ]
        )
        second_role.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["roles"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 6)
        self.assertIn(str(Role.objects.get(name="multi permission role").id), str(response_data))
        self.assertIn(
            str(Role.objects.get(name=constants.GovPermissions.MANAGE_TEAM_ADVICE.name).id), str(response_data)
        )
        self.assertIn(
            str(Role.objects.get(name=constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name).id), str(response_data)
        )
        self.assertIn(
            str(Role.objects.get(name=constants.GovPermissions.REVIEW_GOODS.name).id), str(response_data),
        )

    def test_only_roles_that_a_user_sees_are_roles_with_a_subset_of_the_permissions_of_the_users_own_role_mid(self):
        permissions = [
            constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
            constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
        ]
        user_role = Role(name="new role")
        user_role.permissions.set(permissions)
        user_role.save()
        self.gov_user.role = user_role
        self.gov_user.save()

        # Create a new role, each with a singular different permission
        for permission in Permission.internal.all():
            role = Role(name=str(permission.id))
            role.permissions.set([permission.id])
            role.save()
        second_role = Role(name="multi permission role")
        second_role.permissions.set(
            [
                constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
                constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
                constants.GovPermissions.REVIEW_GOODS.name,
            ]
        )
        second_role.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["roles"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 4)
        self.assertIn(
            str(Role.objects.get(name=constants.GovPermissions.MANAGE_TEAM_ADVICE.name).id), str(response_data)
        )
        self.assertIn(
            str(Role.objects.get(name=constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name).id), str(response_data)
        )

    def test_only_roles_that_a_user_sees_are_roles_with_a_subset_of_the_permissions_of_the_users_own_role_min(self):
        permissions = [constants.GovPermissions.MANAGE_TEAM_ADVICE.name]
        user_role = Role(name="new role")
        user_role.permissions.set(permissions)
        user_role.save()
        self.gov_user.role = user_role
        self.gov_user.save()

        # Create a new role, each with a singular different permission
        for permission in Permission.internal.all():
            role = Role(name=str(permission.id))
            role.permissions.set([permission.id])
            role.save()
        second_role = Role(name="multi permission role")
        second_role.permissions.set(
            [
                constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
                constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
                constants.GovPermissions.REVIEW_GOODS.name,
            ]
        )
        second_role.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["roles"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 3)
        self.assertIn(
            str(Role.objects.get(name=constants.GovPermissions.MANAGE_TEAM_ADVICE.name).id), str(response_data)
        )

    @parameterized.expand(
        [
            [
                [
                    constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
                    constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
                    constants.GovPermissions.REVIEW_GOODS.name,
                ]
            ],
            [
                [
                    constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
                    constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
                ]
            ],
            [[constants.GovPermissions.MANAGE_TEAM_ADVICE.name]],
        ]
    )
    def test_user_can_only_see_permissions_user_already_has_in_current_role(self, permissions):
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
