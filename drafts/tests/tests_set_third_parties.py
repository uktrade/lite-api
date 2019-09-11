from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class ThirdPartiesOnDraft(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.url = reverse('drafts:third_parties', kwargs={'pk': self.draft.id})

    def test_set_and_remove_third_parties_on_draft_successful(self):
        data = {
            'name': 'UK Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'sub_type': 'agent',
            'website': 'https://www.gov.uk'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.draft.third_parties.first().name, 'UK Government')

        tp_pk = self.draft.third_parties.first().pk

        url = reverse('drafts:remove_third_party', kwargs={'pk': self.draft.id, 'tp_pk': tp_pk})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.draft.ultimate_end_users.count(), 0)

    def test_set_multiple_third_parties_on_draft_successful(self):
        data = [
                {
                    'name': 'UK Government',
                    'address': 'Westminster, London SW1A 0AA',
                    'country': 'GB',
                    'sub_type': 'agent',
                    'website': 'https://www.gov.uk'
                },
                {
                    'name': 'French Government',
                    'address': 'Paris',
                    'country': 'FR',
                    'sub_type': 'other',
                    'website': 'https://www.gov.fr'
                }
            ]

        for third_party in data:
            self.client.post(self.url, third_party, **self.exporter_headers)

        self.assertEqual(self.draft.third_parties.count(), 2)

    def test_unsuccessful_add_third_party(self):
        data = {
            'name': 'UK Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'website': 'https://www.gov.uk'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data, {'errors': {'sub_type': ['This field is required.']}})
