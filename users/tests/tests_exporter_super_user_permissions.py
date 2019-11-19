from django.urls import reverse
from rest_framework import status

from conf.constants import Permissions, Roles
from test_helpers.clients import DataTestClient
from users.enums import UserType
from users.models import Permission


class SuperUserTests(DataTestClient):

    def test_super_user_role_cannot_be_edited(self):
        role_id = Roles.EXPORTER_SUPER_USER_ROLE_ID
        url = reverse("organisations:role", kwargs={"pk": role_id, "org_pk": self.organisation.id})

        data = {"permissions": [Permissions.MANAGE_FINAL_ADVICE]}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_exporter_default_user_role_cannot_be_edited(self):
        role_id = Roles.EXPORTER_DEFAULT_ROLE_ID
        url = reverse("organisations:role", kwargs={"pk": role_id, "org_pk": self.organisation.id})

        data = {"permissions": [Permissions.MANAGE_FINAL_ADVICE]}

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_super_user_roles_have_all_permissions(self):
        self.assertEqual(
            self.super_user_role.permissions.count(), Permission.objects.filter(type=UserType.INTERNAL).count()
        )
        self.assertEqual(self.exporter_super_user_role.permissions.count(), Permission.objects.filter(type=UserType.EXPORTER).count())

    def test_cannot_remove_super_user_role_from_yourself(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        data = {"role": self.default_role.id}
        url = reverse("organisations:user", kwargs={"user_pk": self.exporter_user.id, "org_pk": self.organisation.id})

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_super_user_role_can_be_removed_by_a_super_user(self):
        valid_user = self.create_exporter_user(self.organisation)
        valid_user.save()
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        self.exporter_user.save()
        data = {"role": self.default_role.id}
        url = reverse("organisations:user", kwargs={"user_pk": valid_user.id, "org_pk": self.organisation.id})

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_super_user_role_cannot_be_removed_by_someone_without_super_user_role(self):
        valid_user = self.create_exporter_user(self.organisation, role=self.exporter_super_user_role)
        valid_user.save()
        data = {"role": self.default_role.id}
        url = reverse("organisations:user", kwargs={"user_pk": valid_user.id, "org_pk": self.organisation.id})

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_user_can_assign_super_user_role(self):
        valid_user = self.create_exporter_user(self.organisation)
        valid_user.save()
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        self.exporter_user.save()
        data = {"role": self.super_user_role.id}
        url = reverse("organisations:user", kwargs={"user_pk": valid_user.id, "org_pk": self.organisation.id})

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_assign_super_user_without_super_user_role(self):
        valid_user = self.create_exporter_user(self.organisation, role=self.exporter_super_user_role)
        valid_user.save()
        data = {"role": self.super_user_role.id}
        url = reverse("organisations:user", kwargs={"user_pk": valid_user.id, "org_pk": self.organisation.id})

        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
