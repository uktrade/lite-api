from django.urls import reverse
from rest_framework import status

from cases.models import Case, CaseAssignment
from queues.models import Queue

from teams.models import Team
from test_helpers.clients import DataTestClient


class CaseAssignmentTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application', self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.case = Case.objects.get(application=self.application)
        self.default_queue = Queue.objects.get(id='00000000-0000-0000-0000-000000000001')
        self.default_team = Team.objects.get(id='00000000-0000-0000-0000-000000000001')
        self.gov_user = self.create_gov_user('gov1@email.com', team=self.default_team)

    def test_can_assign_a_single_user_to_case_on_a_queue(self):
        data = {
            'users': [self.gov_user.id],
            'cases': [self.case.id]
        }
        url = reverse('queues:case_assignment', kwargs={'pk': self.default_queue.id})
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CaseAssignment.objects.get().users.values_list('id', flat=True)[0], self.gov_user.id)
        self.assertEqual(CaseAssignment.objects.get().cases.values_list('id', flat=True)[0], self.case.id)
        self.assertEqual(CaseAssignment.objects.get().queue.id, self.default_queue.id)

    def test_can_assign_many_users_to_many_cases(self):
        users = [
            self.create_gov_user(email='1@1.1', team=self.default_team),
            self.create_gov_user(email='2@2.2', team=self.default_team),
            self.gov_user
        ]
        cases = [
            self.case,
            Case.objects.get(
                application=self.test_helper.submit_draft(
                    self, self.test_helper.create_draft_with_good_end_user_and_site(
                        'Example Application',
                        self.test_helper.organisation)))
        ]
        data = {
            'users': [gov_user.id for gov_user in users],
            'cases': [case.id for case in cases]
        }
        url = reverse('queues:case_assignment', kwargs={'pk': self.default_queue.id})
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
