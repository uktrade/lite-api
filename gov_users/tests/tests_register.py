from django.urls import path, include, reverse
from rest_framework import status

from gov_users.enums import GovUserStatuses
from gov_users.models import GovUser
from test_helpers.clients import DataTestClient


class GovUserAuthenticateTests(DataTestClient):

    urlpatterns = [
        path('gov-users/', include('gov_users.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    def setUp(self):
        super().setUp()
        self.gov_user_preexisting_count = GovUser.objects.all().count()

    def test_user_registers_new_user(self):
        response = self.client.get(reverse('gov_users:gov_users'), **{'HTTP_GOV_USER_EMAIL': 'jsmith@name.com'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jsmith@name.com',
            'team': self.team.id
        }
        url = reverse('gov_users:gov_users')
        response = self.client.post(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GovUser.objects.all().count(), self.gov_user_preexisting_count + 1)
        new_user = GovUser.objects.get(email='jsmith@name.com')
        self.assertEqual(new_user.status, GovUserStatuses.ACTIVE)
        self.assertEqual(new_user.email, 'jsmith@name.com')
        response = self.client.get(reverse('gov_users:gov_users'), **{'HTTP_GOV_USER_EMAIL': str(new_user.email)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fail_create_new_user(self):
        data = {}
        url = reverse('gov_users:gov_users')
        response = self.client.post(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GovUser.objects.all().count(), self.gov_user_preexisting_count + 0)
