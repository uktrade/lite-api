from django.urls import reverse
from rest_framework import status
from flags.models import Flag

from test_helpers.clients import DataTestClient


class FlagsListTests(DataTestClient):

    url = reverse('flags:flags')

    def test_gov_user_can_see_all_flags(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_gov_user_can_see_filtered_flags(self):
        other_team = self.create_team('Team')

        self.create_flag('Flag1', 'Case', self.team)
        self.create_flag('Flag2', 'Organisation', self.team)
        self.create_flag('Flag3', 'Case', other_team)
        self.create_flag('Flag4', 'Case', self.team)

        response = self.client.get(self.url + '?level=Case&team=' + self.team.name, **self.gov_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['flags']), 2)

    def test_gov_user_can_see_no_flags_when_team_doesnt_exist(self):
        response = self.client.get(self.url + '?level=Case&team=blah', **self.gov_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['flags']), 0)
