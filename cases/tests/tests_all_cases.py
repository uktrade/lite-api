from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class RetrieveAllCases(DataTestClient):
    def setUp(self):
        super().setUp()
        self.team = self.create_team('team team')
        self.queue1 = self.create_queue('queue1', self.team.id)
        self.queue2 = self.create_queue('queue2', self.team.id)
        self.case1 = self.create_application_case('case on new cases queue')
        self.case2 = self.create_application_case('case2 case2 for queue1')
        self.case3 = self.create_application_case('case3 case3 case3 for queue2')

        # TODO
        self.url = reverse('cases:documents', kwargs={'pk': self.case.id})

    def test_get_all_case_assignments(self):
        self.case2.queues = [self.queue1.id]
        self.case2.save()
        self.case3.queues = [self.queue2.id]
        self.case3.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response_data['case_assignments']['cases'].len > 3)

        response_data_contains_case1 = False
        response_data_contains_case2 = False
        response_data_contains_case3 = False
        for case in response_data['case_assignments']['cases']:
            if self.case1.id == case.id:
                response_data_contains_case1 = True
            if self.case2.id == case.id:
                response_data_contains_case2 = True
            if self.case3.id == case.id:
                response_data_contains_case3 = True

        self.assertTrue(response_data_contains_case1)
        self.assertTrue(response_data_contains_case2)
        self.assertTrue(response_data_contains_case3)
