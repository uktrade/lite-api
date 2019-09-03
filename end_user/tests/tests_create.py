from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class EUAETests(DataTestClient):

    url = reverse('end-users:EUAE-query')

    def test_create_EUAE_query_POST(self):
        # Assemble

        organisation = self.create_organisation('TAT')
        end_user = self.create_end_user('endUser', organisation)

        data = {
            'end_user_id': end_user.id,
            'details': 'These are the details',
            'raised_reason': 'I don\'t know'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

        response_data = response.json()
        self.assertIn('id', response_data)
