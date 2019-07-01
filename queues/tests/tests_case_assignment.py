import json

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
            'assignments':
                [
                    {'user': self.gov_user.id, 'case': self.case.id}
                ]
            }

        url = reverse('queues:case_assignment', kwargs={'pk': self.default_queue.id})
        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CaseAssignment.objects.get().user.id, self.gov_user.id)
        self.assertEqual(CaseAssignment.objects.get().case.id, self.case.id)
        self.assertEqual(CaseAssignment.objects.get().queue.id, self.default_queue.id)

    def test_can_assign_many_users_to_many_cases(self):

        user1 = self.create_gov_user(email='1@1.1', team=self.default_team)
        user2 = self.create_gov_user(email='2@2.2', team=self.default_team)
        user3 = self.gov_user

        case1 = self.case
        case2 = Case.objects.get(
            application=self.test_helper.submit_draft(
                self, self.test_helper.create_draft_with_good_end_user_and_site(
                    'Example Application',
                    self.test_helper.organisation)))

        data = {
            'assignments':
                [
                    {'user': user1.id, 'case': case1.id},
                    {'user': user2.id, 'case': case1.id},
                    {'user': user3.id, 'case': case1.id},
                    {'user': user1.id, 'case': case2.id},
                    {'user': user2.id, 'case': case2.id},
                    {'user': user3.id, 'case': case2.id}
                ]
            }

        url = reverse('queues:case_assignment', kwargs={'pk': self.default_queue.id})
        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(CaseAssignment.objects.all()), 6)

    def test_duplicate_relationships_are_not_created(self):
        url = reverse('queues:case_assignment', kwargs={'pk': self.default_queue.id})
        user1 = self.create_gov_user(email='1@1.1', team=self.default_team)
        user2 = self.create_gov_user(email='2@2.2', team=self.default_team)
        user3 = self.gov_user

        case1 = self.case
        case2 = Case.objects.get(
            application=self.test_helper.submit_draft(
                self, self.test_helper.create_draft_with_good_end_user_and_site(
                    'Example Application',
                    self.test_helper.organisation)))

        data = {
            'assignments':
                [
                    {'user': user1.id, 'case': case1.id},
                    {'user': user2.id, 'case': case1.id},
                    {'user': user3.id, 'case': case1.id},
                    {'user': user1.id, 'case': case2.id},
                    {'user': user2.id, 'case': case2.id},
                    {'user': user3.id, 'case': case2.id}
                ]
        }

        response = self.client.post(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(json.loads(response.content)), 6)
        self.assertEqual(len(CaseAssignment.objects.all()), 6)
        data = {
            'assignments':
                [
                    {'user': self.gov_user.id, 'case': self.case.id}
                ]
        }

        response = self.client.post(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(CaseAssignment.objects.all()), 6)
        self.assertEqual(len(json.loads(response.content)), 1)

    def test_all_assignments_are_cleared_when_a_case_leaves_a_queue(self):
        case_assignment = CaseAssignment(user=self.gov_user, queue=self.default_queue, case=self.case)
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
        case_assignment = CaseAssignment(user=self.gov_user, queue=self.default_queue, case=self.case)
        case_assignment.save()

        self.url = reverse('cases:case', kwargs={'pk': self.case.id})

        new_queue = Queue(name='new queue', team=self.team)
        new_queue.save()

        data = {
            'queues': [new_queue.id, self.default_queue.id]
        }

        self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(len(CaseAssignment.objects.all()), 1)

    def test_updating_set_of_assignments(self):
        url = reverse('queues:case_assignment', kwargs={'pk': self.default_queue.id})
        user1 = self.create_gov_user(email='1@1.1', team=self.default_team)
        user2 = self.create_gov_user(email='2@2.2', team=self.default_team)
        user3 = self.gov_user

        case1 = self.case
        case2 = Case.objects.get(
            application=self.test_helper.submit_draft(
                self, self.test_helper.create_draft_with_good_end_user_and_site(
                    'Example Application',
                    self.test_helper.organisation)))

        data = {
            'assignments':
                [
                    {'user': user1.id, 'case': case1.id},
                    {'user': user2.id, 'case': case1.id},
                    {'user': user3.id, 'case': case1.id},
                ]
        }

        self.client.post(url, data, **self.gov_headers)

        data = {
            'assignments':
                [
                    {'user': user1.id, 'case': case1.id},
                    {'user': user1.id, 'case': case2.id},
                    {'user': user2.id, 'case': case2.id},
                    {'user': user3.id, 'case': case2.id}
                ]
            }

        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(CaseAssignment.objects.filter(user=user1)), 2)
        self.assertEqual(len(CaseAssignment.objects.filter(case=case2)), 3)
        self.assertEqual(len(CaseAssignment.objects.filter(case=case1, user=user2)), 0)
