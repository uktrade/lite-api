from django.urls import reverse

from test_helpers.clients import DataTestClient


class TestUserTeamQueue(DataTestClient):
    def setUp(self):
        super().setUp()
        self.second_queue = self.create_queue("second queue", self.team)
        self.url = reverse("users:team_queues", kwargs={"pk": self.gov_user.id})

    def test_get_all_users_team_queues(self):
        response = self.client.get(self.url, **self.gov_headers)
        queues = response.json()["queues"]

        self.assertEqual(len(queues), 2)
        first_queue = queues[0]
        second_queue = queues[1]
        self.assertEqual(first_queue[0], str(self.queue.id))
        self.assertEqual(first_queue[1], str(self.queue.name))
        self.assertEqual(second_queue[0], str(self.second_queue.id))
        self.assertEqual(second_queue[1], str(self.second_queue.name))
