from django.urls import path, include, reverse
from rest_framework import status

from gov_users.models import Permission, Role
from test_helpers.clients import DataTestClient


class RolesAndPermissionsTests(DataTestClient):

    urlpatterns = [
        path('gov-users/', include('gov_users.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    def setUp(self):
        super().setUp()

    def test_create_new_role_with_permission_to_make_final_decisions(self):
        id = Permission.objects.get(name='Make final decisions').id
        data = {
            'name': 'some role',
            'permissions': [id],
        }
        url = reverse('gov_users:roles')
        response = self.client.post(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name='some role').name, 'some role')
