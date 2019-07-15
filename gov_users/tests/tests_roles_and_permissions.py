import json

from django.urls import path, include, reverse
from rest_framework import status

from conf.constants import Permissions
from gov_users.models import Permission, Role
from test_helpers.clients import DataTestClient


class RolesAndPermissionsTests(DataTestClient):

    urlpatterns = [
        path('gov-users/', include('gov_users.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    def setUp(self):
        super().setUp()
        self.url = reverse('gov_users:roles')

    def test_create_new_role_with_permission_to_make_final_decisions(self):
        id = Permission.objects.get(id=Permissions.MAKE_FINAL_DECISIONS).id
        data = {
            'name': 'some role',
            'permissions': [id],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name='some role').name, 'some role')

    def tests_get_list_of_all_roles(self):
        role = Role(name='some')
        role.permissions.set([Permission.objects.get(id=Permissions.MAKE_FINAL_DECISIONS).id])
        role.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['roles']), 2)

    def tests_get_list_of_all_permissions(self):
        url = reverse('gov_users:permissions')
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['permissions']), 1)
