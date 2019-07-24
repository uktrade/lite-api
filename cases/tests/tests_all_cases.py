from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class RetrieveAllCases(DataTestClient):
    def setUp(self):
        super().setUp()
        self.team = self.create_team('team team')
        self.queue1 = self.create_queue('queue1', self.team)
        self.queue2 = self.create_queue('queue2', self.team)
        self.case1 = self.create_application_case('case on new cases queue')
        self.case2 = self.create_application_case('case2 case2 for queue1')
        self.case3 = self.create_application_case('case3 case3 case3 for queue2')

        # TODO
        self.url = reverse('cases:documents', kwargs={'pk': self.case1.id})

    def test_get_all_case_assignments(self):
        self.case2.queues.set([self.queue1.id])
        self.case2.save()
        self.case3.queues.set([self.queue2.id])
        self.case3.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(3, response_data['case_assignments']['cases'].len)

        case_id_list = map(lambda c: c.id, response_data['case_assignments']['cases'])

        self.assertTrue(self.case1.id in case_id_list)
        self.assertTrue(self.case2.id in case_id_list)
        self.assertTrue(self.case3.id in case_id_list)

