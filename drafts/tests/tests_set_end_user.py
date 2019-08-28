from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class EndUserOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.url = reverse('drafts:end_user', kwargs={'pk': self.draft.id})

    @parameterized.expand([
        'government',
        'commercial',
        'other'
    ])
    def test_set_end_user_on_draft_successful(self, data_type):
        data = {
            'name': 'Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'type': data_type,
            'website': 'https://www.gov.uk'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.draft.end_user.name, data['name'])
        self.assertEqual(self.draft.end_user.address, data['address'])
        self.assertEqual(self.draft.end_user.country, get_country(data['country']))
        self.assertEqual(self.draft.end_user.type, data_type)
        self.assertEqual(self.draft.end_user.website, data['website'])

    @parameterized.expand([
        [{}],
        [{
            'name': 'Lemonworld Org',
            'address': '3730 Martinsburg Rd, Gambier, Ohio',
            'country': 'US',
            'website': 'https://www.americanmary.com'
        }],
        [{
            'name': 'Lemonworld Org',
            'address': '3730 Martinsburg Rd, Gambier, Ohio',
            'country': 'US',
            'type': 'business',
            'website': 'https://www.americanmary.com'
        }],
    ])
    def test_set_end_user_on_draft_failure(self, data):
        self.draft = self.create_draft(self.organisation)
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.draft.end_user, None)
