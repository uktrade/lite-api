from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class EditApplicationTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application(self.organisation)
        self.url = reverse('applications:application', kwargs={'pk': self.application.id})
        self.original_last_modified_at = self.application.last_modified_at

    def test_edit_application_name(self):
        data = {'name': 'new app name!'}

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.application.name, data['name'])
        self.assertNotEqual(self.application.last_modified_at, self.original_last_modified_at)

    def test_edit_application_reference_number(self):
        data = {'reference_number_on_information_form': '35236246'}

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.application.reference_number_on_information_form,
                         data['reference_number_on_information_form'])
        self.assertNotEqual(self.application.last_modified_at, self.original_last_modified_at)
