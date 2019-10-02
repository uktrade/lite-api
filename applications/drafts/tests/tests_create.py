from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from applications.models import StandardApplication, OpenApplication
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
            'have_you_been_informed': 'yes',
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StandardApplication.objects.count(), 1)

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
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(OpenApplication.objects.count(), 0)
