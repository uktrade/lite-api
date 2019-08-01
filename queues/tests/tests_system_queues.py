from rest_framework import status

from cases.models import CaseAssignment
from conf.settings import OPEN_CASES_SYSTEM_QUEUE_ID
from test_helpers.clients import DataTestClient
from queues.tests.tests_consts import ALL_CASES_SYSTEM_QUEUE_ID


class RetrieveAllCases(DataTestClient):
    def setUp(self):
        super().setUp()
        self.team = self.create_team('team team')
        self.queue1 = self.create_queue('queue1', self.team)
        self.queue2 = self.create_queue('queue2', self.team)
        self.case1 = self.create_application_case('case1 case1 for queue1')
        self.case2 = self.create_application_case('case2 case2 case2 for queue2')
        self.case3 = self.create_application_case('case3 case3 case3 for queue2')
        self.case3.application.status = 'approved'
        self.case3.application.save(update_fields=['status'])

    def test_get_all_case_assignments(self):
        """
        Given Cases assigned to various queues
        When a user requests the All Cases system queue
        Then all cases are returned regardless of the queues they are assigned to
        """

        # Arrange
        case_assignment = CaseAssignment(queue=self.queue1, case=self.case1)
        case_assignment.save()
        case_assignment = CaseAssignment(queue=self.queue2, case=self.case2)
        case_assignment.save()

        url = '/queues/' + ALL_CASES_SYSTEM_QUEUE_ID + '/case-assignments/'

        # Act
        response = self.client.get(url, **self.gov_headers)

        # Assert
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
        url = '/queues/?include_system_queues=True'

        # Act
        response = self.client.get(url, **self.gov_headers)

        # Assert
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
        url = '/queues/?include_system_queues=False'

        # Act
        response = self.client.get(url, **self.gov_headers)

        # Assert
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

        # Arrange
        url = '/queues/'

        # Act
        response = self.client.get(url, **self.gov_headers)

        # Assert
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

        # Arrange
        url = '/queues/' + ALL_CASES_SYSTEM_QUEUE_ID + '/'

        # Act
        response = self.client.get(url, **self.gov_headers)

        # Assert
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(ALL_CASES_SYSTEM_QUEUE_ID, response_data['queue']['id'])
        self.assertEqual(3, len(response_data['queue']['cases']))

    def test_get_all_cases_system_queue_limits_to_200_cases(self):
        """
        Given that in excess of 200 cases exist
        When a user gets the all cases system queue
        Then 200 cases are returned
        """

        # Arrange
        url = '/queues/' + ALL_CASES_SYSTEM_QUEUE_ID + '/'

        i = 0

        while i <= 300:
            self.create_application_case('Limits case ' + str(i))

            i += 1

        # Act
        response = self.client.get(url, **self.gov_headers)

        # Assert
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(ALL_CASES_SYSTEM_QUEUE_ID, response_data['queue']['id'])

        self.assertEqual(200, len(response_data['queue']['cases']))

        # Test ordering: Cases should be returned newest first
        self.assertEqual('Limits case 101', response_data['queue']['cases'][199]['application']['name'])
        self.assertEqual('Limits case 300', response_data['queue']['cases'][0]['application']['name'])

    def test_get_open_cases_system_queue(self):
        """
        Given that a number of cases exist and are assigned to different user defined queues
        When a user the open cases system queue
        Then only open cases are returned regardless of which user defined queues they are assigned to
        """

        # Arrange
        url = '/queues/' + OPEN_CASES_SYSTEM_QUEUE_ID + '/'

        # Act
        response = self.client.get(url, **self.gov_headers)

        # Assert
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(OPEN_CASES_SYSTEM_QUEUE_ID, response_data['queue']['id'])
        self.assertEqual(2, len(response_data['queue']['cases']))
