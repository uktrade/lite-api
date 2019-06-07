from django.urls import reverse
from rest_framework import status

from departments.models import Department
from test_helpers.clients import DataTestClient


class DepartmentListTests(DataTestClient):

    url = reverse('departments:departments')

    def tests_department_list(self):
        Department(name='name 1').save()
        Department(name='name 2').save()
        Department(name='name 3').save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["departments"]), 3)
