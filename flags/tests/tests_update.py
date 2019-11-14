from django.core.management import call_command
from django.urls import reverse
from rest_framework import status

from flags.enums import FlagStatuses
from test_helpers.clients import DataTestClient


class FlagsUpdateTest(DataTestClient):

    def setUp(self):
        super().setUp()
        # Seed layouts
        call_command('seedsystemflags')

    def test_flag_can_be_deactivated(self):
        flag = self.create_flag('New Flag', 'Case', self.team)

        data = {
            'status': FlagStatuses.DEACTIVATED,
        }

        url = reverse('flags:flag', kwargs={'pk': flag.id})
        response = self.client.put(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['flag']['status'], FlagStatuses.DEACTIVATED)

    def test_flag_cannot_be_deactivated_by_a_user_outside_flags_team(self):
        team = self.create_team('Secondary team')
        flag = self.create_flag('New Flag', 'Case', team)

        data = {
            'status': FlagStatuses.DEACTIVATED,
        }

        url = reverse('flags:flag', kwargs={'pk': flag.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(flag.status, FlagStatuses.ACTIVE)
