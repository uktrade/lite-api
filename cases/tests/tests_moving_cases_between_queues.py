from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.models import Case
from test_helpers.clients import DataTestClient


class MoveCasesTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = Case.objects.get(application=self.standard_application)
        self.url = reverse('cases:case', kwargs={'pk': self.case.id})
        self.queues = [
            self.create_queue('Queue 1', self.team),
            self.create_queue('Queue 2', self.team),
            self.create_queue('Queue 3', self.team),
        ]

    def test_move_case_successful(self):
        data = {
            'queues': [queue.id for queue in self.queues]
        }

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(self.case.queues.values_list('id', flat=True)), set(data['queues']))

    @parameterized.expand([
        # None/Empty Queues
        [{'queues': None}],
        [{'queues': []}],
        # Invalid Queues
        [{'queues': 'Not an array'}],
        [{'queues': ['00000000-0000-0000-0000-000000000002']}],
        [{'queues': ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002']}],
    ])
    def test_move_case_failure(self, data):
        existing_queues = set(self.case.queues.values_list('id', flat=True))

        response = self.client.put(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(self.case.queues.values_list('id', flat=True)), existing_queues)
