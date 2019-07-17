import json

from django.urls import reverse
from rest_framework import status

from users.models import GovUser
from teams.models import Team
from test_helpers.clients import DataTestClient


class UserByTeamListTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.gov_user_preexisting_count = GovUser.objects.all().count()

    def tests_user_by_team_list(self):
        team = Team.objects.get(name='Admin')
        team2 = Team(name='Second')
        team2.save()
        govuser1 = GovUser(email='test2@mail.com', first_name='John', last_name='Smith', team=self.team)
        govuser2 = GovUser(email='test3@mail.com', first_name='John', last_name='Smith', team=team2)
        govuser1.save()
        govuser2.save()
        url = reverse('teams:team_users', kwargs={'pk': team.id})
        response = self.client.get(url, **self.gov_headers)
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['users']), self.gov_user_preexisting_count + 1)
        self.assertContains(response, 'test2@mail.com')
        self.assertNotContains(response, 'test3@mail.com')
