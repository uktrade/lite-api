from rest_framework import status
from rest_framework.reverse import reverse

from drafts.models import Draft
from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):

    url = reverse('drafts:drafts')

    def test_create_draft_success(self):
        """
        Ensure we can create a new draft object
        """
        data = {
            'name': 'Test',
            'licence_type': 'standard_licence',
            'export_type': 'temporary',
            'reference_number_on_information_form': '123'
        }

        response = self.client.post(self.url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Draft.objects.count(), 1)

    def test_create_draft_failure(self):
        """
        Ensure we cannot create a new draft object with an invalid POST
        """
        data = {
            'export_type': 'temporary',
            'reference_number_on_information_form': '123'
        }

        response = self.client.post(self.url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Draft.objects.count(), 0)

    def test_create_draft_failure_2(self):
        """
        Ensure we cannot create a new draft object with an invalid POST
        """
        data = {
            'licence_type': 'standard_licence',
            'reference_number_on_information_form': '123'
        }

        response = self.client.post(self.url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Draft.objects.count(), 0)

    def test_create_draft_failure_3(self):
        """
        Ensure we cannot create a new draft object with an invalid POST
        """
        data = {
            'licence_type': 'standard_licence',
            'export_type': 'temporary',
        }

        response = self.client.post(self.url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Draft.objects.count(), 0)
