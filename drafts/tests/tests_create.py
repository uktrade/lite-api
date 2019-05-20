import json

from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from drafts.models import Draft
from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):

    url = reverse('drafts:drafts')

    def test_create_draft_successful(self):
        """
        Ensure we can create a new draft object
        """
        data = {
            'name': 'Test',
            'licence_type': 'standard_licence',
            'export_type': 'temporary',
            'reference_number_on_information_form': '123',
        }

        response = self.client.post(self.url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Draft.objects.count(), 1)

    @parameterized.expand([
        [{}],
        [{
            'licence_type': 'standard_licence',
            'export_type': 'temporary',
        }],
        [{
            'name': 'Test',
            'export_type': 'temporary',
        }],
        [{
            'name': 'Test',
            'licence_type': 'standard_licence',
        }],
    ])
    def test_create_draft_failure(self, data):
        """
        Ensure we cannot create a new draft object with an invalid POST
        """
        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Draft.objects.count(), 0)
