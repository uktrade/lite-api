import json

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from flags.models import Flag
from teams.models import Team
from test_helpers.clients import DataTestClient


class FlagsCreateTest(DataTestClient):

    url = reverse('flags:flags')

    def test_gov_user_can_create_flags(self):
        data = {
            'name': 'new flag',
            'level': 'Organisation',
        }
        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['flag']['name'], 'new flag')
        self.assertEqual(response_data['flag']['level'], 'Organisation')
        self.assertEqual(response_data['flag']['team'], str(Team.objects.get(name='Admin').id))

    # @parameterized.expand([
    #     [{'data': {'name': ''}}],  # Blank
    #     [{'data': {'name': 'test'}}],  # Case insensitive duplicate names
    #     [{'data': {'name': ' TesT '}}],
    #     [{'data': {'name': 'TEST'}}],
    #     [{'data': {'name': 'a' * 21}}]  # Too long a name
    # ])
    # def test_fail_create_flag(self, data):
    #     flag = Flag(name='Test', level='Case', team=self.team)
    #     flag.save()
    #     response = self.client.post(self.url, data['data'], **self.gov_headers)
    #
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
