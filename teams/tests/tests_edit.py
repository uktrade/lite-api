from django.urls import reverse
from rest_framework import status

from teams.models import Team
from test_helpers.clients import DataTestClient


class TeamEditTests(DataTestClient):

    def tests_edit_team(self):
        team_name = 'Team1'
        Team(name=team_name).save()
        id = Team.objects.filter(name=team_name)[0].id
        data = {
            'name': 'edited team'
        }
        url = reverse('teams:team', kwargs={'pk': id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Team.objects.filter(id=id)[0].name, 'edited team')

    def tests_cannot_rename_to_an_already_used_name_case_insensitive(self):
        Team(name='name').save()
        Team(name='test').save()
        id = Team.objects.get(name='name').id

        data = {
            'name': 'TEST'
        }
        url = reverse('teams:team', kwargs={'pk': id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
