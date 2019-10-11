from django.urls import reverse
from rest_framework import status

from parties.models import ThirdParty
from test_helpers.clients import DataTestClient


class ThirdPartiesOnDraft(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.draft.third_parties.set([])
        self.draft.save()
        self.url = reverse('applications:third_parties', kwargs={'pk': self.draft.id})

    def test_set_and_remove_third_parties_on_draft_successful(self):
        """
        Given a standard draft has been created
        And the draft does not yet contain a third party
        When a new third party is added
        Then the third party is successfully added to the draft
        """

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

        url = reverse('applications:remove_third_party', kwargs={'pk': self.draft.id, 'tp_pk': tp_pk})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.draft.ultimate_end_users.count(), 0)

    def test_set_third_parties_on_draft_open_application_failure(self):
        pre_test_third_party_count = ThirdParty.objects.all().count()
        data = {
            'name': 'UK Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'sub_type': 'agent',
            'website': 'https://www.gov.uk'
        }
        open_draft = self.create_open_draft(self.organisation)
        url = reverse('applications:third_parties', kwargs={'pk': open_draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(ThirdParty.objects.all().count(), pre_test_third_party_count)

    def test_set_multiple_third_parties_on_draft_successful(self):
        """
        Given a standard draft has been created
        And the draft does not yet contain a third party
        When multiple third parties are added
        Then all third parties are successfully added to the draft
        """

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
        """
         Given a standard draft has been created
         And the draft does not yet contain a third party
         When attempting to add an invalid third party
         Then the third party is not added to the draft
         """

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

    def test_get_third_parties(self):
        third_party = self.create_third_party('third party', self.organisation)
        third_party.save()
        self.draft.third_parties.add(third_party)
        self.draft.save()

        response = self.client.get(self.url, **self.exporter_headers)
        third_parties = response.json()['third_parties']

        self.assertEqual(len(third_parties), 1)
        self.assertEqual(third_parties[0]['id'], str(third_party.id))
        self.assertEqual(third_parties[0]['name'], str(third_party.name))
        self.assertEqual(third_parties[0]['country']['name'], str(third_party.country.name))
        self.assertEqual(third_parties[0]['website'], str(third_party.website))
        self.assertEqual(third_parties[0]['type'], str(third_party.type))
        self.assertEqual(third_parties[0]['organisation'], str(third_party.organisation.id))
        self.assertEqual(third_parties[0]['sub_type'], str(third_party.sub_type))

    def test_set_third_parties_on_draft_open_application_failure(self):
        """
        Given a draft open application
        When I try to add a third party to the application
        Then a 404 NOT FOUND is returned
        And no third parties have been added
        """
        # assemble
        pre_test_third_party_count = ThirdParty.objects.all().count()
        data = {
            'name': 'UK Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'sub_type': 'agent',
            'website': 'https://www.gov.uk'
        }
        open_draft = self.create_open_draft(self.organisation)
        url = reverse('applications:third_parties', kwargs={'pk': open_draft.id})

        # act
        response = self.client.post(url, data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(ThirdParty.objects.all().count(), pre_test_third_party_count)
