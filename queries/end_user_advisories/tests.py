from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from cases.models import Case
from test_helpers.clients import DataTestClient


class EndUserAdvisoryViewTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.url = reverse('queries:end_user_advisories:end_user_advisories')

    def test_view_end_user_advisory_query(self):
        self.create_end_user_advisory('a note', 'because I\'m unsure', self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()['end_user_advisories']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response_data), 1)


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
        self.assertEqual(Case.objects.count(), 1)

    @parameterized.expand([
        ('com', 'person', 'http://gov.co.uk', 'place street', 'GB', '', ''),  # invalid end user type
        ('commercial', '', '', 'nowhere', 'GB', '', ''),  # name is empty
        ('government', 'abc', 'abc', 'nowhere', 'GB', '', ''),  # invalid web address
        ('government', 'abc', '', '', 'GB', '', ''),  # empty address
        ('government', 'abc', '', 'nowhere', 'ALP', '', ''),  # invalid country code
        ('', '', '', '', '', '', ''),  # empty dataset
    ])
    def test_create_end_user_advisory_query_failure(self, end_user_type, name, website, address, country, note, reasoning):
        data = {
            'end_user': {
                'type': end_user_type,
                'name': name,
                'website': website,
                'address': address,
                'country': country,
            },
            'note': note,
            'reasoning': reasoning,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
