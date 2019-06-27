from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.models import Case
from teams.models import Team
from test_helpers.clients import DataTestClient


class AssigningUsers(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application', self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.case = Case.objects.get(application=self.application)
        self.url = reverse('cases:case', kwargs={'pk': self.case.id})
        self.team = Team.objects.get()
        self.users = [
            self.create_gov_user('email1@gov.uk', self.team),
            self.create_gov_user('email2@gov.uk', self.team),
            self.create_gov_user('email3@gov.uk', self.team),
        ]

    def test_move_case_successful(self):
        data = {
            'users': [gov_user.id for gov_user in self.users]
        }

        response = self.client.put(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(self.case.users.values_list('id', flat=True)), set(data['users']))

    @parameterized.expand([
        # None/Empty Gov Users
        [{'users': None}],
        # Invalid Gov Users
        [{'users': 'Not an array'}],
        [{'users': ['00000000-0000-0000-0000-000000000002']}],
        [{'users': ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002']}],
    ])
    def test_move_case_failure(self, data):
        existing_users = set(self.case.users.values_list('id', flat=True))

        response = self.client.put(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(self.case.users.values_list('id', flat=True)), existing_users)
