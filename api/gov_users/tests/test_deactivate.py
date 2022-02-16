from django.urls import reverse
from rest_framework import status

from api.gov_users.enums import GovUserStatuses
from api.users.tests.factories import GovUserFactory
from test_helpers.clients import DataTestClient
from api.users.libraries.user_to_token import user_to_token
from api.users.models import GovUser


class GovUserDeactivateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.valid_user = GovUserFactory(
            baseuser_ptr__email="test2@mail.com",
            baseuser_ptr__first_name="John",
            baseuser_ptr__last_name="Smith",
            team=self.team,
        )
        self.valid_user.save()

    def test_deactivate_a_user(self):
        data = {"status": "Deactivated"}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.valid_user.pk})
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            GovUser.objects.get(pk=self.valid_user.pk).status,
            GovUserStatuses.DEACTIVATED,
        )

    def test_cannot_deactivate_self(self):
        data = {"status": "Deactivated"}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.gov_user.pk})
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deactivate_and_reactivate_a_user(self):
        url = reverse("gov_users:gov_users")
        response = self.client.get(url, **{"HTTP_GOV_USER_TOKEN": user_to_token(self.valid_user.baseuser_ptr)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = {"status": "Deactivated"}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.valid_user.pk})
        self.client.put(url, data, **self.gov_headers)
        response = self.client.get(
            reverse("gov_users:gov_users"), **{"HTTP_GOV_USER_TOKEN": user_to_token(self.valid_user.baseuser_ptr)}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = {"status": "Active"}
        self.client.put(url, data, **self.gov_headers)
        response = self.client.get(
            reverse("gov_users:gov_users"), **{"HTTP_GOV_USER_TOKEN": user_to_token(self.valid_user.baseuser_ptr)}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_deactivate_a_super_user(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        self.valid_user.role = self.super_user_role
        self.valid_user.save()

        data = {"status": "Deactivated"}

        url = reverse("gov_users:gov_user", kwargs={"pk": self.valid_user.pk})

        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
