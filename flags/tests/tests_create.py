from django.core.management import call_command
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from flags.enums import FlagLevels
from test_helpers.clients import DataTestClient


class FlagsCreateTest(DataTestClient):

    url = reverse('flags:flags')

    def setUp(self):
        super().setUp()
        # Seed layouts
        call_command('seedsystemflags')

    def test_gov_user_can_create_flags(self):
        data = {
            'name': 'new flag',
            'level': 'Organisation',
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['flag']['name'], 'new flag')
        self.assertEqual(response_data['flag']['level'], 'Organisation')
        self.assertEqual(response_data['flag']['team'], {
            'id': str(self.team.id),
            'name': self.team.name
        })

    @parameterized.expand([
        [''],  # Blank
        ['test'],  # Case insensitive duplicate names
        [' TesT '],
        ['TEST'],
        ['a' * 21]  # Too long a name
    ])
    def test_create_flag_failure(self, name):
        self.create_flag('test', FlagLevels.CASE, self.team)

        response = self.client.post(self.url, {'name': name}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
