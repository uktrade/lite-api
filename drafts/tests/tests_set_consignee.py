from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from parties.models import Consignee
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class ConsigneeOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.url = reverse('drafts:consignee', kwargs={'pk': self.draft.id})

    @parameterized.expand([
        'government',
        'commercial',
        'other'
    ])
    def test_set_consignee_on_draft_successful(self, data_type):
        data = {
            'name': 'Government of Paraguay',
            'address': 'Asuncion',
            'country': 'PY',
            'sub_type': data_type,
            'website': 'https://www.gov.py'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.draft.consignee.name, data['name'])
        self.assertEqual(self.draft.consignee.address, data['address'])
        self.assertEqual(self.draft.consignee.country, get_country(data['country']))
        self.assertEqual(self.draft.consignee.sub_type, data_type)
        self.assertEqual(self.draft.consignee.website, data['website'])

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
            'sub_type': 'made-up',
            'website': 'https://www.americanmary.com'
        }],
    ])
    def test_set_consignee_on_draft_failure(self, data):
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.draft.consignee, None)

    def test_consignee_deleted_when_new_one_added(self):
        """
        Given a standard draft has been created
        And the draft contains a consignee
        When a new consignee is added
        Then the old one is removed
        """
        # assemble
        consignee1 = self.create_consignee('old consignee', self.organisation)
        self.draft.consignee = consignee1
        self.draft.save()
        new_consignee = {
            'name': 'Government of Paraguay',
            'address': 'Asuncion',
            'country': 'PY',
            'sub_type': 'government',
            'website': 'https://www.gov.py'
        }

        # act
        self.client.post(self.url, new_consignee, **self.exporter_headers)

        # assert
        self.draft.refresh_from_db()
        consignee2 = self.draft.consignee

        self.assertNotEqual(consignee2, consignee1)
        with self.assertRaises(Consignee.DoesNotExist):
            Consignee.objects.get(id=consignee1.id)
