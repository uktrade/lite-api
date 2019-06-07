from django.urls import reverse
from rest_framework import status

from departments.models import Department
from test_helpers.clients import DataTestClient


class DepartmentEditTests(DataTestClient):

    def tests_edit_department(self):
        Department(name='name 1').save()
        id = Department.objects.get().id
        self.assertEqual(Department.objects.get().name, 'name 1')
        data = {
            'name': 'edited department'
        }
        url = reverse('departments:department', kwargs={'pk': id})
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Department.objects.get().name, 'edited department')

    def tests_cannot_rename_to_an_already_used_name_case_insensitive(self):
        Department(name='name').save()
        Department(name='test').save()
        id = Department.objects.get(name='name').id

        data = {
            'name': 'TEST'
        }
        url = reverse('departments:department', kwargs={'pk': id})
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
