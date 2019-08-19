from django.urls import reverse
from rest_framework import status

from teams.models import Team
from test_helpers.clients import DataTestClient
from users.models import GovUser


class UserByTeamListTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.gov_user_preexisting_count = GovUser.objects.all().count()
        self.team = self.gov_user.team

    def tests_view_user_by_team(self):
        """
        Tests that a valid gov user can see a specific team's members
        """
        team2 = Team(name='Second')
        team2.save()

        GovUser(email='test2@mail.com', first_name='John', last_name='Smith', team=self.team).save()
        GovUser(email='test3@mail.com', first_name='John', last_name='Smith', team=team2).save()

        url = reverse('teams:team_users', kwargs={'pk': self.team.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['users']), self.gov_user_preexisting_count + 1)
        self.assertContains(response, 'test2@mail.com')
        self.assertNotContains(response, 'test3@mail.com')
