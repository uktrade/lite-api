from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from conf import constants
from conf.constants import ExporterPermissions
from test_helpers.clients import DataTestClient
from users.enums import UserType
from users.models import Role, Permission, ExporterUser


class RolesAndPermissionsTests(DataTestClient):
    def test_create_new_role_with_no_permissions(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        data = {"name": "some role", "permissions": []}

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

        data = {"permissions": [ExporterPermissions.ADMINISTER_USERS.name]}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            ExporterPermissions.ADMINISTER_USERS.name
            in Role.objects.get(id=role.id).permissions.values_list("id", flat=True)
        )

    def test_cannot_create_role_without_permission(self):
        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})
        data = {"name": "some role", "permissions": []}
        initial_roles_count = Role.objects.count()

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Role.objects.all().count(), initial_roles_count)

    def test_cannot_edit_role_without_permission(self):
        role = Role(name="some", organisation=self.organisation, type=UserType.EXPORTER)
        role.save()
        url = reverse("organisations:role", kwargs={"org_pk": self.organisation.id, "pk": role.id})

        data = {"permissions": [ExporterPermissions.ADMINISTER_USERS.name]}

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

        data = {"name": role_name, "permissions": []}

        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.filter(name=role_name).count(), 2)

    def test_only_see_roles_user_has_all_permissions_for_3_permissions(self):
        permissions = [
            constants.ExporterPermissions.ADMINISTER_USERS.name,
            constants.ExporterPermissions.ADMINISTER_SITES.name,
            constants.ExporterPermissions.EXPORTER_ADMINISTER_ROLES.name,
        ]
        user_role = Role(name="new role", organisation=self.organisation)
        user_role.permissions.set(permissions)
        user_role.save()
        self.exporter_user.set_role(self.organisation, user_role)
        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})

        # Create a new role, each with a singular different permission
        for permission in Permission.exporter.all():
            role = Role(name=str(permission.id), organisation=self.organisation)
            role.permissions.set([permission.id])
            role.save()

        second_role = Role(name="multi permission role", organisation=self.organisation)
        second_role.permissions.set(
            [
                constants.ExporterPermissions.ADMINISTER_USERS.name,
                constants.ExporterPermissions.ADMINISTER_SITES.name,
                constants.ExporterPermissions.EXPORTER_ADMINISTER_ROLES.name,
            ]
        )
        second_role.save()

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 6)
        self.assertIn(str(Role.objects.get(name="multi permission role").id), str(response_data))
        self.assertIn(
            str(Role.objects.get(name=constants.ExporterPermissions.ADMINISTER_USERS.name).id), str(response_data)
        )
        self.assertIn(
            str(Role.objects.get(name=constants.ExporterPermissions.ADMINISTER_SITES.name).id), str(response_data)
        )
        self.assertIn(
            str(Role.objects.get(name=constants.ExporterPermissions.EXPORTER_ADMINISTER_ROLES.name).id),
            str(response_data),
        )

    def test_only_see_roles_user_has_all_permissions_for_2_permissions(self):
        permissions = [
            constants.ExporterPermissions.ADMINISTER_USERS.name,
            constants.ExporterPermissions.ADMINISTER_SITES.name,
        ]
        user_role = Role(name="new role", organisation=self.organisation)
        user_role.permissions.set(permissions)
        user_role.save()
        self.exporter_user.set_role(self.organisation, user_role)
        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})

        # Create a new role, each with a singular different permission
        for permission in Permission.exporter.all():
            role = Role(name=str(permission.id), organisation=self.organisation)
            role.permissions.set([permission.id])
            role.save()

        second_role = Role(name="multi permission role", organisation=self.organisation)
        second_role.permissions.set(
            [
                constants.ExporterPermissions.ADMINISTER_USERS.name,
                constants.ExporterPermissions.ADMINISTER_SITES.name,
                constants.ExporterPermissions.EXPORTER_ADMINISTER_ROLES.name,
            ]
        )
        second_role.save()

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 4)
        self.assertIn(
            str(Role.objects.get(name=constants.ExporterPermissions.ADMINISTER_USERS.name).id), str(response_data)
        )
        self.assertIn(
            str(Role.objects.get(name=constants.ExporterPermissions.ADMINISTER_SITES.name).id), str(response_data)
        )

    def test_only_see_roles_user_has_all_permissions_for_1_permission(self):
        permissions = [constants.ExporterPermissions.ADMINISTER_USERS.name]
        user_role = Role(name="new role", organisation=self.organisation)
        user_role.permissions.set(permissions)
        user_role.save()
        self.exporter_user.set_role(self.organisation, user_role)
        url = reverse("organisations:roles_views", kwargs={"org_pk": self.organisation.id})

        # Create a new role, each with a singular different permission
        for permission in Permission.exporter.all():
            role = Role(name=str(permission.id), organisation=self.organisation)
            role.permissions.set([permission.id])
            role.save()

        second_role = Role(name="multi permission role", organisation=self.organisation)
        second_role.permissions.set(
            [
                constants.ExporterPermissions.ADMINISTER_USERS.name,
                constants.ExporterPermissions.ADMINISTER_SITES.name,
                constants.ExporterPermissions.EXPORTER_ADMINISTER_ROLES.name,
            ]
        )
        second_role.save()

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 3)
        self.assertIn(
            str(Role.objects.get(name=constants.ExporterPermissions.ADMINISTER_USERS.name).id), str(response_data)
        )

    @parameterized.expand(
        [
            [
                [
                    constants.ExporterPermissions.ADMINISTER_USERS.name,
                    constants.ExporterPermissions.ADMINISTER_SITES.name,
                    constants.ExporterPermissions.EXPORTER_ADMINISTER_ROLES.name,
                ]
            ],
            [
                [
                    constants.ExporterPermissions.ADMINISTER_USERS.name,
                    constants.ExporterPermissions.ADMINISTER_SITES.name,
                ]
            ],
            [[constants.ExporterPermissions.ADMINISTER_USERS.name]],
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
        user_role.permissions.set([constants.ExporterPermissions.ADMINISTER_USERS.name])
        user_role.save()
        self.exporter_user.set_role(self.organisation, user_role)

        response = self.client.put(
            reverse("organisations:user", kwargs={"org_pk": self.organisation.id, "user_pk": self.exporter_user.id},),
            data={"role": str(constants.Roles.EXPORTER_DEFAULT_ROLE_ID)},
            **self.exporter_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(
            self.exporter_user.get_role(self.organisation),
            Role.objects.get(id=constants.Roles.EXPORTER_DEFAULT_ROLE_ID),
        )

    def test_cannot_change_another_users_role_to_one_the_request_user_does_not_have_access_to(self):
        user_role = Role(name="new role", organisation=self.organisation)
        user_role.permissions.set([constants.ExporterPermissions.ADMINISTER_USERS.name])
        user_role.save()
        second_user_role = Role(name="new role", organisation=self.organisation)
        second_user_role.permissions.set(
            [constants.ExporterPermissions.ADMINISTER_USERS.name, constants.ExporterPermissions.ADMINISTER_SITES.name]
        )
        second_user_role.save()
        self.exporter_user.set_role(self.organisation, user_role)
        second_user = self.create_exporter_user(self.organisation)

        response = self.client.put(
            reverse("organisations:user", kwargs={"org_pk": self.organisation.id, "user_pk": second_user.id},),
            data={"role": str(second_user_role.id)},
            **self.exporter_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(second_user.get_role(self.organisation), second_user_role)

    def test_can_change_another_users_role_to_newly_created_role(self):
        user_role = Role(name="new role one", organisation=self.organisation, type=UserType.EXPORTER)
        user_role.permissions.set([constants.ExporterPermissions.ADMINISTER_USERS.name])
        user_role.save()

        second_user_role = Role(name="new role two", organisation=self.organisation, type=UserType.EXPORTER)
        second_user_role.save()

        self.exporter_user.set_role(self.organisation, user_role)
        second_user = self.create_exporter_user(self.organisation)

        response = self.client.put(
            reverse("organisations:user", kwargs={"org_pk": self.organisation.id, "user_pk": second_user.id},),
            data={"role": second_user_role.id},
            **self.exporter_headers,
        )

        response_body = response.json()
        second_user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(second_user.get_role(self.organisation), user_role)
        self.assertEqual(response_body["user_relationship"]["role"], str(second_user_role.id))
        self.assertEqual(response_body["user_relationship"]["status"]["key"], "Active")
        self.assertEqual(response_body["user_relationship"]["status"]["value"], "Active")
