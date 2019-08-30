from django.urls import reverse

from conf.settings import OPEN_CASES_SYSTEM_QUEUE_ID
from queues.tests.tests_consts import ALL_MY_QUEUES_ID, ALL_CASES_SYSTEM_QUEUE_ID
from test_helpers.clients import DataTestClient


class RetrieveAllMyCases(DataTestClient):

    def setUp(self):
        super().setUp()
        team_2 = self.create_team('team 2')

        self.queue1 = self.create_queue('queue1', self.team)
        self.queue2 = self.create_queue('queue2', self.team)
        self.queue3 = self.create_queue('queue3', team_2)

        self.case1 = self.create_standard_application_case(self.exporter_user.organisation)
        self.case2 = self.create_standard_application_case(self.exporter_user.organisation)
        self.case3 = self.create_standard_application_case(self.exporter_user.organisation)
        self.case4 = self.create_standard_application_case(self.exporter_user.organisation)

        self.case1.queues.set([self.queue1.id])
        self.case2.queues.set([self.queue1.id, self.queue2.id])
        self.case3.queues.set([self.queue2.id])
        self.case4.queues.set([self.queue3.id])

        self.url=reverse('queues:queue', kwargs={'pk': ALL_MY_QUEUES_ID})

    def test_can_see_all_cases_in_teams_queues(self):
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()['queue']

        self.assertEqual(len(response_data['cases']), 3)

    def test_queues_return_number_of_contents(self):
        response = self.client.get(reverse('queues:queues') + '?include_system_queues=True', **self.gov_headers)
        response_data = response.json()['queues']
        print(response_data)

        i = 0
        for queue in response_data:
            if queue['id'] in str(self.queue1.id):
                i += 1
                self.assertEqual(queue['cases_count'], 2)
            if queue['id'] in str(self.queue2.id):
                i += 1
                self.assertEqual(queue['cases_count'], 2)
            if queue['id'] in str(self.queue3.id):
                i += 1
                self.assertEqual(queue['cases_count'], 1)
            if queue['id'] in ALL_MY_QUEUES_ID:
                i += 1
                self.assertEqual(queue['cases_count'], 3)
            if queue['id'] in ALL_CASES_SYSTEM_QUEUE_ID:
                i += 1
                self.assertEqual(queue['cases_count'], 4)
            if queue['id'] in OPEN_CASES_SYSTEM_QUEUE_ID:
                i += 1
                self.assertEqual(queue['cases_count'], 4)

        # Asserts that the assertions have all run
        self.assertEqual(i, 6)
