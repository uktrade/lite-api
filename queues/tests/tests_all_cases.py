from rest_framework import status

from cases.models import CaseAssignment
from test_helpers.clients import DataTestClient
from queues.tests.tests_consts import ALL_CASES_SYSTEM_QUEUE_ID


class RetrieveAllCases(DataTestClient):
    def setUp(self):
        super().setUp()
        self.team = self.create_team('team team')
        self.queue1 = self.create_queue('queue1', self.team)
        self.queue2 = self.create_queue('queue2', self.team)
        self.case1 = self.create_application_case('case2 case2 for queue1')
        self.case2 = self.create_application_case('case3 case3 case3 for queue2')

    def test_get_all_case_assignments(self):
        case_assignment = CaseAssignment(queue=self.queue1, case=self.case1)
        case_assignment.save()
        case_assignment = CaseAssignment(queue=self.queue2, case=self.case2)
        case_assignment.save()

        url = '/queues/' + ALL_CASES_SYSTEM_QUEUE_ID + '/case-assignments/'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response_data['case_assignments']))

        case_id_list = [c['case'] for c in response_data['case_assignments']]

        self.assertTrue(str(self.case1.id) in case_id_list)
        self.assertTrue(str(self.case2.id) in case_id_list)