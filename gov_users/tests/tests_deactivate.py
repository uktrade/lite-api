from django.urls import reverse
from rest_framework import status

from gov_users.enums import GovUserStatuses
from users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient
from users.models import GovUser


class GovUserDeactivateTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.valid_user = GovUser(email='test2@mail.com', first_name='John', last_name='Smith', team=self.team)
        self.valid_user.save()

    def test_deactivate_a_user(self):
        data = {
            'status': 'Deactivated'
        }
        url = reverse('gov_users:gov_user', kwargs={'pk': self.valid_user.id})
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GovUser.objects.get(id=self.valid_user.id).status, GovUserStatuses.DEACTIVATED)

    def test_cannot_deactivate_self(self):
        data = {
            'status': 'Deactivated'
        }
        url = reverse('gov_users:gov_user', kwargs={'pk': self.gov_user.id})
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deactivate_and_reactivate_a_user(self):
        url = reverse('gov_users:gov_users')
        response = self.client.get(url, **{'HTTP_GOV_USER_TOKEN': user_to_token(self.valid_user)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = {
            'status': 'Deactivated'
        }
        url = reverse('gov_users:gov_user', kwargs={'pk': self.valid_user.id})
        self.client.put(url, data, **self.gov_headers)
        response = self.client.get(reverse('gov_users:gov_users'), **{'HTTP_GOV_USER_TOKEN': user_to_token(self.valid_user)})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = {
            'status': 'Active'
        }
        self.client.put(url, data, **self.gov_headers)
        response = self.client.get(reverse('gov_users:gov_users'), **{'HTTP_GOV_USER_TOKEN': user_to_token(self.valid_user)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

