from django.urls import reverse
from parameterized import parameterized
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

    def test_edit_a_role(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        role = Role(name="some", organisation=self.organisation, type=UserType.EXPORTER)
        role.save()
        url = reverse("organisations:role", kwargs={"org_pk": self.organisation.id, "pk": role.id})

        data = {"permissions": [Permissions.ADMINISTER_USERS]}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Permissions.ADMINISTER_USERS in Role.objects.get(id=role.id).permissions.values_list("id", flat=True)
        )

    def test_cannot_create_role_without_permission(self):
        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})
        data = {
            "name": "some role",
            "permissions": [],
        }
        initial_roles_count = Role.objects.count()

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Role.objects.all().count(), initial_roles_count)

    def test_cannot_edit_role_without_permission(self):
        role = Role(name="some", organisation=self.organisation, type=UserType.EXPORTER)
        role.save()
        url = reverse("organisations:role", kwargs={"org_pk": self.organisation.id, "pk": role.id})

        data = {"permissions": [Permissions.ADMINISTER_USERS]}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Role.objects.get(id=role.id).permissions.values().count(), 0)

    @parameterized.expand(
        [
            [{"name": "this is a name", "permissions": []}],
            [{"name": "ThIs iS A NaMe", "permissions": []}],
            [{"name": " this is a name    ", "permissions": []}],
        ]
    )
    def test_role_name_must_be_unique(self, data):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        Role(name="this is a name", organisation=self.organisation).save()
        initial_roles_count = Role.objects.count()

        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Role.objects.all().count(), initial_roles_count)

    def test_role_name_not_have_to_be_unique_different_organisations(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        org, _ = self.create_organisation_with_exporter_user()
        role_name = "duplicate name"
        Role(name=role_name, organisation=org, type=UserType.EXPORTER).save()

        data = {
            "name": role_name,
            "permissions": [],
        }

        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.filter(name=role_name).count(), 2)

    @parameterized.expand(
        [
            [[Permissions.ADMINISTER_USERS, Permissions.ADMINISTER_SITES, Permissions.EXPORTER_ADMINISTER_ROLES]],
            [[Permissions.ADMINISTER_USERS, Permissions.ADMINISTER_SITES]],
            [[Permissions.ADMINISTER_USERS]],
        ]
    )
    def test_only_see_roles_user_has_all_permissions_for(self, permissions):
        user_role = Role(name="new role", organisation=self.organisation)
        user_role.permissions.set(permissions)
        user_role.save()
        self.exporter_user.set_role(self.organisation, user_role)
        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})

        i = 0
        # Create a new role, each with a singular different permission
        for permission in Permission.exporter.all():
            role = Role(name="name: " + str(i), organisation=self.organisation)
            role.permissions.set([permission.id])
            role.save()
            i += 1
        second_role = Role(name="multi permission role", organisation=self.organisation)
        second_role.permissions.set([Permissions.ADMINISTER_USERS, Permissions.ADMINISTER_SITES, Permissions.EXPORTER_ADMINISTER_ROLES])
        second_role.save()
        # Adjust expected result to cover the multi permission role
        r = 1 if len(permissions) == 3 else 0

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["results"]

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
        user_role = Role(name="new role", organisation=self.organisation)
        user_role.permissions.set(permissions)
        user_role.save()
        self.exporter_user.set_role(self.organisation, user_role)

        url = reverse("organisations:permissions")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["permissions"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(permissions))
        for permission in permissions:
            self.assertIn(permission, [p["id"] for p in response_data])

    def test_cannot_change_own_role(self):
        user_role = Role(name="new role", organisation=self.organisation)
        user_role.permissions.set([Permissions.ADMINISTER_USERS])
        user_role.save()
        self.exporter_user.set_role(self.organisation, user_role)

        response = self.client.put(
            reverse(
                "organisations:user",
                kwargs={"org_pk": self.organisation.id, "user_pk": self.exporter_user.id},
            ),
            data={"role": str(Roles.EXPORTER_DEFAULT_ROLE_ID)},
            **self.exporter_headers
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_change_another_users_role_to_one_the_request_user_does_not_have_access_to(self):
        user_role = Role(name="new role", organisation=self.organisation)
        user_role.permissions.set([Permissions.ADMINISTER_USERS])
        user_role.save()
        second_user_role = Role(name="new role", organisation=self.organisation)
        second_user_role.permissions.set([Permissions.ADMINISTER_USERS, Permissions.ADMINISTER_SITES])
        second_user_role.save()
        self.exporter_user.set_role(self.organisation, user_role)
        second_user = self.create_exporter_user(self.organisation)

        response = self.client.put(
            reverse(
                "organisations:user",
                kwargs={"org_pk": self.organisation.id, "user_pk": second_user.id},
            ),
            data={"role": str(second_user_role.id)},
            **self.exporter_headers
            )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
