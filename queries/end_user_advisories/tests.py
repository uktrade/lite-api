from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from cases.models import Case
from test_helpers.clients import DataTestClient


class EndUserAdvisoryViewTests(DataTestClient):

    def test_view_end_user_advisory_queries(self):
        """
        Ensure that the user can view all end user advisory queries
        """
        self.create_end_user_advisory('a note', 'because I am unsure', self.organisation)

        response = self.client.get(reverse('queries:end_user_advisories:end_user_advisories'),
                                   **self.exporter_headers)
        response_data = response.json()['end_user_advisories']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response_data), 1)

    def test_view_end_user_advisory_query(self):
        """
        Ensure that the user can view an end user advisory query
        """
        query = self.create_end_user_advisory('a note', 'because I am unsure', self.organisation)

        response = self.client.get(reverse('queries:end_user_advisories:end_user_advisory',
                                           kwargs={'pk': query.id}), **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EndUserAdvisoryCreateTests(DataTestClient):

    url = reverse('queries:end_user_advisories:end_user_advisories')

    def test_create_end_user_advisory_query(self):
        """
        Ensure that a user can create an end user advisory, and that it creates a case
        when doing so
        """
        data = {
            'end_user': {
                'sub_type': 'government',
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
        self.assertEqual(end_user_data['sub_type'], data['end_user']['sub_type'])
        self.assertEqual(end_user_data['name'], data['end_user']['name'])
        self.assertEqual(end_user_data['website'], data['end_user']['website'])
        self.assertEqual(end_user_data['address'], data['end_user']['address'])
        self.assertEqual(end_user_data['country']['id'], data['end_user']['country'])
        self.assertEqual(Case.objects.count(), 1)

    def test_create_copied_end_user_advisory_query(self):
        """
        Ensure that a user can duplicate an end user advisory, it links to the previous
        query and that it creates a case when doing so
        """
        query = self.create_end_user_advisory('Advisory', '', self.organisation)
        data = {
            'end_user': {
                'sub_type': 'government',
                'name': 'Ada',
                'website': 'https://gov.uk',
                'address': '123',
                'country': 'GB',
            },
            'note': 'I Am Easy to Find',
            'reasoning': 'Lack of hairpin turns',
            'copy_of': query.id,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()['end_user_advisory']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['note'], data['note'])
        self.assertEqual(response_data['reasoning'], data['reasoning'])
        self.assertEqual(response_data['copy_of']['reference_code'], data['copy_of'])

        end_user_data = response_data['end_user']
        self.assertEqual(end_user_data['sub_type'], data['end_user']['sub_type'])
        self.assertEqual(end_user_data['name'], data['end_user']['name'])
        self.assertEqual(end_user_data['website'], data['end_user']['website'])
        self.assertEqual(end_user_data['address'], data['end_user']['address'])
        self.assertEqual(end_user_data['country']['id'], data['end_user']['country'])
        self.assertEqual(Case.objects.count(), 2)

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
