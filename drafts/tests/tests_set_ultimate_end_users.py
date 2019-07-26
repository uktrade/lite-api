from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class UltimateEndUsersOnDraft(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = OrgAndUserHelper.complete_draft('Goods test', self.test_helper.organisation)
        self.url = reverse('drafts:ultimate_end_users', kwargs={'pk': self.draft.id})

    def test_set_and_remove_ultimate_end_user_on_draft_successful(self):
        data = {
            'name': 'UK Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'type': 'commercial',
            'website': 'https://www.gov.uk'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.draft.ultimate_end_users[0].name, 'UK Government')

        data = {
            'id': str(self.draft.ultimate_end_users[0].id)
        }

        response = self.client.delete(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.draft.ultimate_end_users), 0)

    def test_set_multiple_ultimate_end_users_on_draft_successful(self):
        data = {
            'ultimate_end_user': {
                'name': 'UK Government',
                'address': 'Westminster, London SW1A 0AA',
                'country': 'GB',
                'type': 'commercial',
                'website': 'https://www.gov.uk'
            },
            'ultimate_end_user': {
                'name': 'French Government',
                'address': 'Paris',
                'country': 'FR',
                'type': 'government',
                'website': 'https://www.gov.fr'
            }
        }

        for ultimate_end_user in data['ultimate_end_user']:
            self.client.post(self.url, ultimate_end_user, **self.exporter_headers)

        self.assertEqual(len(self.draft.ultimate_end_users), 2)

    def test_unsuccessful_add_ultimate_end_user(self):
        data = {
            'name': 'UK Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'website': 'https://www.gov.uk'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
