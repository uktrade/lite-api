from django.urls import reverse
from rest_framework import status

from teams.models import Team
from test_helpers.clients import DataTestClient


class TeamEditTests(DataTestClient):

    def tests_edit_team(self):
        Team(name='name 1').save()
        id = Team.objects.get().id
        self.assertEqual(Team.objects.get().name, 'name 1')
        data = {
            'name': 'edited team'
        }
        url = reverse('teams:team', kwargs={'pk': id})
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Team.objects.get().name, 'edited team')

    def tests_cannot_rename_to_an_already_used_name_case_insensitive(self):
        Team(name='name').save()
        Team(name='test').save()
        id = Team.objects.get(name='name').id

        data = {
            'name': 'TEST'
        }
        url = reverse('teams:team', kwargs={'pk': id})
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
