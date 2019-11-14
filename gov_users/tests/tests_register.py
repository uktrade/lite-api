from django.urls import reverse
from rest_framework import status

from conf.constants import Roles
from gov_users.enums import GovUserStatuses
from test_helpers.clients import DataTestClient
from users.models import GovUser


class GovUserAuthenticateTests(DataTestClient):

    def test_user_registers_new_user(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jsmith@name.com',
            'team': self.team.id,
            'role': Roles.DEFAULT_ROLE_ID
        }

        url = reverse('gov_users:gov_users')
        response = self.client.post(url, data, **self.gov_headers)
        new_user = GovUser.objects.get(email='jsmith@name.com')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(new_user.status, GovUserStatuses.ACTIVE)
        self.assertEqual(new_user.email, 'jsmith@name.com')

    def test_create_new_user_failure(self):
        self.gov_user_preexisting_count = GovUser.objects.all().count()

        url = reverse('gov_users:gov_users')
        response = self.client.post(url, {}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GovUser.objects.all().count(), self.gov_user_preexisting_count)

    def test_super_user_can_create_new_super_user(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jsmith@name.com',
            'team': self.team.id,
            'role': Roles.SUPER_USER_ROLE_ID
        }

        url = reverse('gov_users:gov_users')
        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_super_user_cannot_create_new_super_user(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jsmith@name.com',
            'team': self.team.id,
            'role': Roles.SUPER_USER_ROLE_ID
        }

        url = reverse('gov_users:gov_users')
        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
