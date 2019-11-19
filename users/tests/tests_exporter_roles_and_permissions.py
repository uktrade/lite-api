from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from conf.constants import Permissions
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
        self.assertEqual(len(response_data["results"]), 2)

    def test_get_list_of_all_roles_as_exporter_super_user(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        initial_roles_count = Role.objects.filter(type=UserType.EXPORTER).count()

        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})

        role = Role(name="some", organisation=self.organisation, type=UserType.EXPORTER)
        role.save()

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), initial_roles_count + 1)

    def test_get_list_of_all_permissions(self):
        url = reverse("organisations:permissions")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["permissions"]), Permission.objects.exporter().count())

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

    @parameterized.expand(
        [
            [{"name": "this is a name", "permissions": []}],
            [{"name": "ThIs iS A NaMe", "permissions": []}],
            [{"name": " this is a name    ", "permissions": []}],
        ]
    )
    def test_role_name_must_be_unique(self, data):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        initial_roles_count = Role.objects.count()
        Role(name="this is a name", organisation=self.organisation).save()

        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(Role.objects.all().count(), initial_roles_count + 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_role_name_not_have_to_be_unique_different_organisations(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        org, _ = self.create_organisation_with_exporter_user()
        role_name = "duplicate name"
        Role(name=role_name, organisation=org).save()

        data = {
            "name": role_name,
            "permissions": [],
        }

        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
