import json

from django.urls import reverse
from rest_framework import status

from cases.models import Case, CaseAssignment
from queues.callbacks import Callbacks
from queues.models import Queue
from teams.models import Team
from test_helpers.clients import DataTestClient


class CaseAssignmentTests(DataTestClient):

    url = reverse('queues:case_assignment', kwargs={'pk': '00000000-0000-0000-0000-000000000001'})

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application',
                                                                               self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.default_queue = Queue.objects.get(id='00000000-0000-0000-0000-000000000001')
        self.default_team = Team.objects.get(id='00000000-0000-0000-0000-000000000001')

        # Cases
        self.case = Case.objects.get(application=self.application)
        self.case2 = Case.objects.get(
            application=self.test_helper.submit_draft(
                self, self.test_helper.create_draft_with_good_end_user_and_site(
                    'Example Application',
                    self.test_helper.organisation)))
        self.case3 = Case.objects.get(
            application=self.test_helper.submit_draft(
                self, self.test_helper.create_draft_with_good_end_user_and_site(
                    'Example Application',
                    self.test_helper.organisation)))

        # Users
        self.gov_user = self.create_gov_user('gov1@email.com', team=self.default_team)
        self.gov_user2 = self.create_gov_user(email='1@1.1', team=self.default_team)
        self.gov_user3 = self.create_gov_user(email='2@2.2', team=self.default_team)

    def test_can_assign_a_single_user_to_case_on_a_queue(self):
        data = {
            'case_assignments': [
                {
                    'case_id': self.case.id,
                    'users': [self.gov_user.id]
                }
            ]
        }

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CaseAssignment.objects.get().case.id, self.case.id)
        self.assertEqual(CaseAssignment.objects.get().queue.id, self.default_queue.id)
        self.assertEqual(CaseAssignment.objects.get().users.values_list('id', flat=True)[0],
                         data['case_assignments'][0]['users'][0])

    def test_can_assign_many_users_to_many_cases(self):
        data = {
            'case_assignments': [
                {
                    'case_id': self.case.id,
                    'users': [
                        self.gov_user.id,
                        self.gov_user2.id,
                        self.gov_user3.id
                    ]
                },
                {
                    'case_id': self.case2.id,
                    'users': [
                        self.gov_user.id,
                        self.gov_user2.id,
                        self.gov_user3.id
                    ]
                }
            ]
        }

        url = reverse('queues:case_assignment', kwargs={'pk': self.default_queue.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(CaseAssignment.objects.all()), 2)
        self.assertEqual(len(CaseAssignment.objects.all()[0].users.values_list('id', flat=True)), 3)
        self.assertEqual(len(CaseAssignment.objects.all()[1].users.values_list('id', flat=True)), 3)

    def test_all_assignments_are_cleared_when_a_case_leaves_a_queue(self):
        case_assignment = CaseAssignment(queue=self.default_queue, case=self.case)
        case_assignment.users.set([self.gov_user])
        case_assignment.save()

        new_queue = Queue(name='new queue', team=self.team)
        new_queue.save()

        self.url = reverse('cases:case', kwargs={'pk': self.case.id})

        data = {
            'queues': [new_queue.id]
        }

        self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(len(CaseAssignment.objects.all()), 0)

    def test_assignments_persist_if_queue_is_not_removed_from_a_queue(self):
        case_assignment = CaseAssignment(queue=self.default_queue, case=self.case)
        case_assignment.users.set([self.gov_user])
        case_assignment.save()

        self.url = reverse('cases:case', kwargs={'pk': self.case.id})

        new_queue = Queue(name='new queue', team=self.team)
        new_queue.save()

        data = {
            'queues': [new_queue.id, self.default_queue.id]
        }

        self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(len(CaseAssignment.objects.all()), 1)

    def test_empty_set_clears_assignments(self):
        case_assignment = CaseAssignment(queue=self.default_queue, case=self.case)
        case_assignment.users.set([self.gov_user])
        case_assignment.save()

        data = {
            'case_assignments': [
                {
                    'case_id': self.case.id,
                    'users': []
                }
            ]
        }
        self.client.put(self.url, data, **self.gov_headers)
        self.assertEqual(len(CaseAssignment.objects.get().users.values_list('id')), 0)

    def test_can_see_lists_of_users_assigned_to_each_case(self):
        data = {
            'case_assignments': [
                {
                    'case_id': self.case.id,
                    'users': [
                        self.gov_user.id,
                        self.gov_user2.id,
                        self.gov_user3.id
                    ]
                },
                {
                    'case_id': self.case2.id,
                    'users': [
                        self.gov_user.id,
                        self.gov_user2.id
                    ]
                }
            ]
        }

        url = reverse('queues:case_assignment', kwargs={'pk': self.default_queue.id})
        self.client.put(url, data, **self.gov_headers)
        response = self.client.get(url, **self.gov_headers)
        case_assignments_response_data = json.loads(response.content)['case_assignments']
        i = 0
        for case_assignment in case_assignments_response_data:
            if case_assignment['case'] == str(self.case.id):
                i += 1
                self.assertEqual(len(case_assignment['users']), 3)
            if case_assignment['case'] == str(self.case2.id):
                i += 1
                self.assertEqual(len(case_assignment['users']), 2)

        # Checks both cases have been checked
        self.assertEqual(i, 2)

    def test_deactivated_user_is_removed_from_assignments(self):
        case_assignment = CaseAssignment(queue=self.default_queue, case=self.case)
        case_assignment.users.set([self.gov_user])
        case_assignment.save()
        case_assignment = CaseAssignment(queue=self.default_queue, case=self.case2)
        case_assignment.users.set([self.gov_user, self.gov_user2])
        case_assignment.save()
        case_assignment = CaseAssignment(queue=self.default_queue, case=self.case3)
        case_assignment.users.set([self.gov_user2])
        
