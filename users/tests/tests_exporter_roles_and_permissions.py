from django.test import tag
from django.urls import reverse
from rest_framework import status

from conf.constants import Permissions, Roles
from test_helpers.clients import DataTestClient
from users.enums import UserType
from users.models import Role, Permission


class RolesAndPermissionsTests(DataTestClient):

    def test_create_new_role_with_no_permissions(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        data = {
            "name": "some role",
            "permissions": [],
        }

        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name="some role").name, "some role")

    def test_get_list_of_all_roles_as_non_exporter_super_user(self):
        role = Role(name="some", organisation=self.organisation, type=UserType.EXPORTER)
        role.permissions.set([Permissions.ADMINISTER_USERS])
        role.save()

        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["roles"]), 2)

    def test_get_list_of_all_roles_as_exporter_super_user(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        initial_roles_count = Role.objects.filter(type=UserType.EXPORTER).count()

        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})

        role = Role(name="some", organisation=self.organisation, type=UserType.EXPORTER)
        role.save()

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["roles"]), initial_roles_count + 1)

    def test_get_list_of_all_permissions(self):
        url = reverse("organisations:permissions")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["permissions"]), Permission.objects.filter(type=UserType.EXPORTER).count())

    def test_edit_a_role(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        role = Role(name="some", organisation=self.organisation, type=UserType.EXPORTER)
        role.save()
        url = reverse("organisations:role", kwargs={"org_pk": self.organisation.id, "pk": role.id})

        data = {"permissions": [Permissions.ADMINISTER_USERS]}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Permissions.ADMINISTER_USERS
            in Role.objects.get(id=role.id).permissions.values_list("id", flat=True)
        )

    def test_cannot_create_role_without_permission(self):
        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})
        data = {
            "name": "some role",
            "permissions": [],
        }

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_edit_role_without_permission(self):
        role = Role(name="some", organisation=self.organisation, type=UserType.EXPORTER)
        role.save()
        url = reverse("organisations:role", kwargs={"org_pk": self.organisation.id, "pk": role.id})

        data = {"permissions": [Permissions.ADMINISTER_USERS]}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
