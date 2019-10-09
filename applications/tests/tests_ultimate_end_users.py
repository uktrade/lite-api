from django.urls import reverse
from rest_framework import status

from parties.models import UltimateEndUser
from test_helpers.clients import DataTestClient


class UltimateEndUsersOnDraft(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.url = reverse('applications:ultimate_end_users', kwargs={'pk': self.draft.id})

    def test_set_and_remove_ultimate_end_user_on_draft_successful(self):
        data = {
            'name': 'UK Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'sub_type': 'commercial',
            'website': 'https://www.gov.uk'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.draft.ultimate_end_users.first().name, 'UK Government')

        ueu_id = self.draft.ultimate_end_users.first().id

        url = reverse('applications:remove_ultimate_end_user', kwargs={'pk': self.draft.id, 'ueu_pk': ueu_id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.draft.ultimate_end_users.count(), 0)

    def test_set_multiple_ultimate_end_users_on_draft_successful(self):
        data = [
                {
                    'name': 'UK Government',
                    'address': 'Westminster, London SW1A 0AA',
                    'country': 'GB',
                    'sub_type': 'commercial',
                    'website': 'https://www.gov.uk'
                },
                {
                    'name': 'French Government',
                    'address': 'Paris',
                    'country': 'FR',
                    'sub_type': 'government',
                    'website': 'https://www.gov.fr'
                }
            ]

        for ultimate_end_user in data:
            self.client.post(self.url, ultimate_end_user, **self.exporter_headers)

        self.assertEqual(self.draft.ultimate_end_users.count(), 2)

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
        self.assertEqual(response_data, {'errors': {'sub_type': ['This field is required.']}})

    def test_get_ultimate_end_users(self):
        ultimate_end_user = self.create_ultimate_end_user('ultimate end user', self.organisation)
        ultimate_end_user.save()
        self.draft.ultimate_end_users.add(ultimate_end_user)
        self.draft.save()

        response = self.client.get(self.url, **self.exporter_headers)
        ultimate_end_users = response.json()['ultimate_end_users']

        self.assertEqual(len(ultimate_end_users), 1)
        self.assertEqual(ultimate_end_users[0]['id'], str(ultimate_end_user.id))
        self.assertEqual(ultimate_end_users[0]['name'], str(ultimate_end_user.name))
        self.assertEqual(ultimate_end_users[0]['country']['name'], str(ultimate_end_user.country.name))
        self.assertEqual(ultimate_end_users[0]['website'], str(ultimate_end_user.website))
        self.assertEqual(ultimate_end_users[0]['type'], str(ultimate_end_user.type))
        self.assertEqual(ultimate_end_users[0]['organisation'], str(ultimate_end_user.organisation.id))
        self.assertEqual(ultimate_end_users[0]['sub_type']['key'], str(ultimate_end_user.sub_type))

    def test_set_ueu_on_draft_open_application_failure(self):
        pre_test_ueu_count = UltimateEndUser.objects.all().count()
        data = {
            'name': 'UK Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'sub_type': 'commercial',
            'website': 'https://www.gov.uk'
        }

        open_draft = self.create_open_draft(self.organisation)
        url = reverse('applications:ultimate_end_users', kwargs={'pk': open_draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(UltimateEndUser.objects.all().count(), pre_test_ueu_count)
