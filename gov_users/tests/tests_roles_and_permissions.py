from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from conf.constants import Permissions
from users.models import Role
from test_helpers.clients import DataTestClient


class RolesAndPermissionsTests(DataTestClient):

    url = reverse('gov_users:roles')

    def test_create_new_role_with_permission_to_make_final_decisions(self):
        data = {
            'name': 'some role',
            'permissions': [Permissions.MAKE_FINAL_DECISIONS],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name='some role').name, 'some role')

    def test_create_new_role_with_no_permissions(self):
        data = {
            'name': 'some role',
            'permissions': [],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.get(name='some role').name, 'some role')

    def tests_get_list_of_all_roles(self):
        role = Role(name='some')
        role.permissions.set([Permissions.MAKE_FINAL_DECISIONS])
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

    def tests_edit_a_role(self):
        role_id = '00000000-0000-0000-0000-000000000001'
        url = reverse('gov_users:role', kwargs={'pk': role_id})

        data = {
            'permissions': [Permissions.MAKE_FINAL_DECISIONS]
        }

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Permissions.MAKE_FINAL_DECISIONS in
                        Role.objects.get(id=role_id).permissions.values_list('id', flat=True))

    @parameterized.expand([
        [{
            'name': 'this is a name',
            'permissions': []
        }],
        [{
            'name': 'ThIs iS A NaMe',
            'permissions': []
        }],
        [{
            'name': ' this is a name    ',
            'permissions': []
        }],
    ])
    def tests_role_name_must_be_unique(self, data):
        Role(name='this is a name').save()

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(Role.objects.all().count(), 2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
