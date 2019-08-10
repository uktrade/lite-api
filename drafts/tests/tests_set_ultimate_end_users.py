from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class UltimateEndUsersOnDraft(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.exporter_user.organisation)
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
        self.assertTrue('UK Government' in self.draft.ultimate_end_users.values_list()[0])

        id = self.draft.ultimate_end_users.values_list()[0][0]

        url = reverse('drafts:remove_ultimate_end_users', kwargs={'pk': self.draft.id, 'ueu_pk': str(id)})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.draft.ultimate_end_users.values_list()), 0)

    def test_set_multiple_ultimate_end_users_on_draft_successful(self):
        data = [
                {
                    'name': 'UK Government',
                    'address': 'Westminster, London SW1A 0AA',
                    'country': 'GB',
                    'type': 'commercial',
                    'website': 'https://www.gov.uk'
                },
                {
                    'name': 'French Government',
                    'address': 'Paris',
                    'country': 'FR',
                    'type': 'government',
                    'website': 'https://www.gov.fr'
                }
            ]

        for ultimate_end_user in data:
            self.client.post(self.url, ultimate_end_user, **self.exporter_headers)

        self.assertEqual(len(self.draft.ultimate_end_users.values_list()), 2)

    def test_unsuccessful_add_ultimate_end_user(self):
        data = {
            'name': 'UK Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'website': 'https://www.gov.uk'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data, {'errors': {'type': ['This field is required.']}})
