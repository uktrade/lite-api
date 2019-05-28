import json

from django.urls import reverse
from rest_framework import status

from departments.models import Department
from test_helpers.clients import DataTestClient


class DepartmentCreateTests(DataTestClient):

    url = reverse('departments:departments')

    def tests_create_department(self):
        data = {
            'name': 'new department'
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Department.objects.get().name, 'new department')

    def tests_department_name_must_be_unique(self):
        Department(name='this is a name').save()
        data = {
            'name': 'this is a name'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(Department.objects.all().count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tests_department_name_must_be_unique_case_insensitive(self):
        Department(name='this is a name').save()
        data = {
            'name': 'ThIs iS A NaMe'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(Department.objects.all().count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
