from django.urls import reverse
from rest_framework import status

from cases.models import Case, CaseAssignment
from queues.models import Queue
from test_helpers.clients import DataTestClient


class CaseAssignmentTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application(self.organisation)

        # Cases
        self.case = Case.objects.get(application=self.application)
        self.case2 = self.create_standard_application_case(self.organisation)
        self.case3 = self.create_standard_application_case(self.organisation)

        # Users
        self.gov_user = self.create_gov_user('gov1@email.com', team=self.team)
        self.gov_user2 = self.create_gov_user(email='1@1.1', team=self.team)
        self.gov_user3 = self.create_gov_user(email='2@2.2', team=self.team)

        self.url = reverse('queues:case_assignments', kwargs={'pk': self.queue.id})

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
        self.assertEqual(CaseAssignment.objects.get().queue.id, self.queue.id)
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

        url = reverse('queues:case_assignments', kwargs={'pk': self.queue.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(CaseAssignment.objects.all()), 2)
        self.assertEqual(len(CaseAssignment.objects.all()[0].users.values_list('id', flat=True)), 3)
        self.assertEqual(len(CaseAssignment.objects.all()[1].users.values_list('id', flat=True)), 3)

    def test_all_assignments_are_cleared_when_a_case_leaves_a_queue(self):
        self.queue.cases.add(self.case)

        case_assignment = CaseAssignment(queue=self.queue, case=self.case)
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
        case_assignment = CaseAssignment(queue=self.queue, case=self.case)
        case_assignment.users.set([self.gov_user])
        case_assignment.save()

        self.url = reverse('cases:case', kwargs={'pk': self.case.id})

        new_queue = Queue(name='new queue', team=self.team)
        new_queue.save()

        data = {
            'queues': [new_queue.id, self.queue.id]
        }

        self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(len(CaseAssignment.objects.all()), 1)

    def test_empty_set_clears_assignments(self):
        case_assignment = CaseAssignment(queue=self.queue, case=self.case)
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

        url = reverse('queues:case_assignments', kwargs={'pk': self.queue.id})
        self.client.put(url, data, **self.gov_headers)
        response = self.client.get(url, **self.gov_headers)
        case_assignments_response_data = response.json()['case_assignments']
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
        case_assignment = CaseAssignment(queue=self.queue, case=self.case)
        case_assignment.users.set([self.gov_user])
        case_assignment.save()

        case_assignment2 = CaseAssignment(queue=self.queue, case=self.case2)
        case_assignment2.users.set([self.gov_user, self.gov_user2])
        case_assignment2.save()

        case_assignment3 = CaseAssignment(queue=self.queue, case=self.case3)
        case_assignment3.users.set([self.gov_user2])
        case_assignment3.save()

        self.assertEqual(len(case_assignment.users.values_list()), 1)
        self.assertEqual(len(case_assignment2.users.values_list()), 2)
        self.assertEqual(len(case_assignment3.users.values_list()), 1)

        # Deactivate initial gov user
        data = {
            'status': 'Deactivated'
        }
        url = reverse('gov_users:gov_user', kwargs={'pk': self.gov_user.id})
        self.client.put(url, data, **self.gov_headers)

        # Ensure that the deactivated user has been removed from all cases
        self.assertEqual(len(self.gov_user.case_assignments.values_list()), 0)
        self.assertEqual(len(case_assignment.users.values_list()), 0)
        self.assertEqual(len(case_assignment2.users.values_list()), 1)
        self.assertEqual(len(case_assignment3.users.values_list()), 1)
