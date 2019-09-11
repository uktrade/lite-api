from django.test import tag
from django.urls import reverse
from rest_framework import status

from cases.models import CaseAssignment
from queues.constants import ALL_CASES_SYSTEM_QUEUE_ID, OPEN_CASES_SYSTEM_QUEUE_ID, MY_TEAMS_QUEUES_CASES_ID
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status
from test_helpers.clients import DataTestClient


class RetrieveAllCases(DataTestClient):

    def setUp(self):
        super().setUp()
        self.queue1 = self.create_queue('queue1', self.team)
        self.queue2 = self.create_queue('queue2', self.team)

        self.case1 = self.create_standard_application_case(self.organisation)
        self.case2 = self.create_standard_application_case(self.organisation)
        self.case3 = self.create_standard_application_case(self.organisation)

        self.case3.application.status = get_case_status_from_status(CaseStatusEnum.FINALISED)
        self.case3.application.save(update_fields=['status'])

        self.url = reverse('queues:queues')
        self.all_cases_system_queue_url = reverse('queues:queue', kwargs={'pk': ALL_CASES_SYSTEM_QUEUE_ID})
        self.open_cases_system_queue_url = reverse('queues:queue', kwargs={'pk': OPEN_CASES_SYSTEM_QUEUE_ID})
        self.my_team_queues_cases_system_queue_url = reverse('queues:queue', kwargs={'pk': MY_TEAMS_QUEUES_CASES_ID})

    def test_get_all_case_assignments(self):
        """
        Given Cases assigned to various queues
        When a user requests the All Cases system queue
        Then all cases are returned regardless of the queues they are assigned to
        """
        case_assignment = CaseAssignment(queue=self.queue1, case=self.case1)
        case_assignment.save()
        case_assignment = CaseAssignment(queue=self.queue2, case=self.case2)
        case_assignment.save()

        url = reverse('queues:case_assignments', kwargs={'pk': OPEN_CASES_SYSTEM_QUEUE_ID})

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response_data['case_assignments']))

        case_id_list = [c['case'] for c in response_data['case_assignments']]

        self.assertTrue(str(self.case1.id) in case_id_list)
        self.assertTrue(str(self.case2.id) in case_id_list)

    def test_get_all_queues_including_true_system_queues_param(self):
        """
        Given that a number of user defined queues exist
        When a user requests queues including system queues
        Then all user defined queues and system queues are returned
        """

        # Arrange
        url = self.url + '?include_system_queues=True'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        queue_id_list = [q['id'] for q in response_data['queues']]
        self.assertTrue(ALL_CASES_SYSTEM_QUEUE_ID in queue_id_list)
        self.assertTrue(OPEN_CASES_SYSTEM_QUEUE_ID in queue_id_list)

    def test_get_all_queues_including_false_system_queues_param(self):
        """
        Given that a number of user defined queues exist
        When a user requests queues not including system queues
        Then all user defined queues are returned
        And system queues are not returned
        """

        # Arrange
        url = self.url + '?include_system_queues=False'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        queue_id_list = [q['id'] for q in response_data['queues']]
        self.assertFalse(ALL_CASES_SYSTEM_QUEUE_ID in queue_id_list)
        self.assertFalse(OPEN_CASES_SYSTEM_QUEUE_ID in queue_id_list)

    def test_get_all_queues_without_system_queues_param(self):
        """
        Given that a number of user defined queues exists
        When a user requests queues and does not indicate if system queues should be included
        Then all user defined queues are returned
        And system queues are not returned
        """
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        queue_id_list = [q['id'] for q in response_data['queues']]
        self.assertFalse(ALL_CASES_SYSTEM_QUEUE_ID in queue_id_list)
        self.assertFalse(OPEN_CASES_SYSTEM_QUEUE_ID in queue_id_list)

    def test_get_all_cases_system_queue(self):
        """
        Given that a number of cases exist and are assigned to different user defined queues
        When a user gets the all cases system queue
        Then all cases are returned regardless of which user defined queues they are assigned to
        """
        response = self.client.get(self.all_cases_system_queue_url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(ALL_CASES_SYSTEM_QUEUE_ID, response_data['queue']['id'])
        self.assertEqual(response_data['queue']['cases_count'], 3)

    def test_get_open_cases_system_queue_returns_expected_cases(self):
        """
        Given that a number of open and closed cases exist
        When a user gets the open cases system queue
        Then only open cases are returned
        """
        response = self.client.get(self.open_cases_system_queue_url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response_data['queue']['id'], OPEN_CASES_SYSTEM_QUEUE_ID)
        self.assertEqual(response_data['queue']['cases_count'], 2)

    def test_get_all_my_team_queues_cases(self):
        """
        Tests that only a team's queue's cases are returned
        when calling that system queue
        """
        team_2 = self.create_team('team 2')

        self.queue1 = self.create_queue('queue1', self.team)
        self.queue2 = self.create_queue('queue2', self.team)
        self.queue3 = self.create_queue('queue3', team_2)

        # Cases 1, 2 and 3 belong to the user's team's queues,
        # whereas case 4 does not
        self.case4 = self.create_standard_application_case(self.organisation)

        self.case1.queues.set([self.queue1.id])
        self.case2.queues.set([self.queue1.id, self.queue2.id])
        self.case3.queues.set([self.queue2.id])
        self.case4.queues.set([self.queue3.id])

        response = self.client.get(self.my_team_queues_cases_system_queue_url, **self.gov_headers)
        response_data = response.json()['queue']

        self.assertEqual(response_data['cases_count'], 3)
