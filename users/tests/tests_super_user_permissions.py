from django.urls import reverse
from rest_framework import status

from conf.constants import Permissions
from test_helpers.clients import DataTestClient
from users.models import Permission, GovUser


class SuperUserTests(DataTestClient):
    """
    Other related tests in:
        'gov_users/tests/tests_deactivate'
            for cannot deactive a super user
        'gov_users/tests/tests_roles_and_permissions'
            for actions requiring the role administrator permission
    """

    def test_super_user_role_cannot_be_edited(self):
        role_id = "00000000-0000-0000-0000-000000000002"
        url = reverse("gov_users:role", kwargs={"pk": role_id})

        data = {"permissions": [Permissions.MANAGE_FINAL_ADVICE]}

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_super_user_role_has_all_permissions(self):
        self.assertEqual(self.super_user_role.permissions.count(), Permission.objects.all().count())

    def test_cannot_remove_super_user_role_from_yourself(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        data = {"role": self.default_role.id}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.gov_user.id})

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_super_user_role_can_be_removed_by_a_super_user(self):
        valid_user = GovUser(
            email="test2@mail.com", first_name="John", last_name="Smith", team=self.team, role=self.super_user_role,
        )
        valid_user.save()
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        data = {"role": self.default_role.id}
        url = reverse("gov_users:gov_user", kwargs={"pk": valid_user.id})

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_super_user_role_cannot_be_removed_by_someone_without_super_user_role(self):
        valid_user = GovUser(
            email="test2@mail.com", first_name="John", last_name="Smith", team=self.team, role=self.super_user_role,
        )
        valid_user.save()
        data = {"role": self.default_role.id}
        url = reverse("gov_users:gov_user", kwargs={"pk": valid_user.id})

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_user_can_assign_super_user_role(self):
        valid_user = GovUser(
            email="test2@mail.com", first_name="John", last_name="Smith", team=self.team, role=self.super_user_role,
        )
        valid_user.save()
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        data = {"role": self.super_user_role.id}
        url = reverse("gov_users:gov_user", kwargs={"pk": valid_user.id})

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_assign_super_user_without_super_user_role(self):
        valid_user = GovUser(
            email="test2@mail.com", first_name="John", last_name="Smith", team=self.team, role=self.super_user_role,
        )
        valid_user.save()
        data = {"role": self.super_user_role.id}
        url = reverse("gov_users:gov_user", kwargs={"pk": valid_user.id})

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
