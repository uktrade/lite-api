from django.test import tag
from django.urls import reverse
from rest_framework import status

from conf.constants import Permissions, Roles
from test_helpers.clients import DataTestClient
from users.enums import UserType
from users.models import Role, Permission


class RolesAndPermissionsTests(DataTestClient):

    url = reverse("gov_users:roles_views")

    @tag('only')
    def test_create_new_role_with_no_permissions(self):
        print(self.exporter_user.get_role(self.organisation))
        self.exporter_user.update_role(self.organisation, self.exporter_super_user_role)
        print(self.exporter_user.get_role(self.organisation))
        data = {
            "name": "some role",
            "permissions": [],
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name="some role").name, "some role")

    def test_get_list_of_all_roles_as_non_exporter_super_user(self):
        role = Role(name="some")
        role.permissions.set([Permissions.ADMINISTER_USERS])
        role.save()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["roles"]), 2)

    def test_get_list_of_all_roles_as_exporter_super_user(self):
        self.exporter_user.role = self.exporter_super_user_role
        self.exporter_user.save()
        role = Role(name="some", organisation=self.organisation)
        initial_roles_count = Role.objects.filter(type=UserType.EXPORTER).count()
        role.permissions.set([Permissions.ADMINISTER_USERS])
        role.save()

        role = Role(name="some", organisation=self.organisation)
        role.save()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["roles"]), initial_roles_count + 1)

    def test_get_list_of_all_permissions(self):
        url = reverse("gov_users:permissions")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["permissions"]), Permission.objects.count())

    def test_edit_a_role(self):
        self.exporter_user.role = self.exporter_super_user_role
        self.exporter_user.save()
        role_id = Roles.EXPORTER_DEFAULT_ROLE_ID
        url = reverse("gov_users:role", kwargs={"pk": role_id})

        data = {"permissions": [Permissions.ADMINISTER_USERS]}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Permissions.ADMINISTER_USERS
            in Role.objects.get(id=role_id).permissions.values_list("id", flat=True)
        )

    def test_cannot_create_role_without_permission(self):
        data = {
            "name": "some role",
            "permissions": [],
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_edit_role_without_permission(self):
        role_id = Roles.EXPORTER_DEFAULT_ROLE_ID
        url = reverse("gov_users:role", kwargs={"pk": role_id})

        data = {"permissions": [Permissions.ADMINISTER_USERS]}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
