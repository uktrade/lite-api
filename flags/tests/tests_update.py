from django.urls import reverse
from rest_framework import status

from flags.enums import FlagStatuses
from flags.models import Flag
from teams.models import Team
from test_helpers.clients import DataTestClient


class FlagsUpdateTest(DataTestClient):

    def test_flag_can_be_deactivated(self):
        flag = Flag(name='New Flag', level='Case', team=self.team)
        flag.save()

        data = {
            'status': FlagStatuses.DEACTIVATED,
        }

        url = reverse('flags:flag', kwargs={'pk': flag.id})
        response = self.client.put(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['flag']['status'], FlagStatuses.DEACTIVATED)

    def test_flag_cannot_be_deactivated_by_a_user_outside_flags_team(self):
        team = Team(name='secondary')
        team.save()
        flag = Flag(name='New Flag', level='Case', team=team)
        flag.save()

        data = {
            'status': FlagStatuses.DEACTIVATED,
        }

        url = reverse('flags:flag', kwargs={'pk': flag.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Flag.objects.get(name='New Flag').status, FlagStatuses.ACTIVE)
