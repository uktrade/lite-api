from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class EndUserAdvisoryViewTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.url = reverse('queries:end_user_advisories:end_user_advisories')

    def test_create_end_user_advisory_query(self):
        # TODO: Create an end user advisory query

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()['end_user_advisories']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response_data['end_user_advisories'], 1)


class EndUserAdvisoryCreateTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.url = reverse('queries:end_user_advisories:end_user_advisories')

    def test_create_end_user_advisory_query(self):
        data = {
            'end_user': {
                'type': 'government',
                'name': 'Ada',
                'website': 'https://gov.uk',
                'address': '123',
                'country': 'GB',
            },
            'note': 'I Am Easy to Find',
            'reasoning': 'Lack of hairpin turns',
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()['end_user_advisory']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['note'], data['note'])
        self.assertEqual(response_data['reasoning'], data['reasoning'])

        end_user_data = response_data['end_user']
        self.assertEqual(end_user_data['type']['key'], data['end_user']['type'])
        self.assertEqual(end_user_data['name'], data['end_user']['name'])
        self.assertEqual(end_user_data['website'], data['end_user']['website'])
        self.assertEqual(end_user_data['address'], data['end_user']['address'])
        self.assertEqual(end_user_data['country']['id'], data['end_user']['country'])

    def test_create_end_user_advisory_query_failure(self):
        data = {}

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()['errors']

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
