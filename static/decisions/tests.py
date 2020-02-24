from rest_framework import status
from rest_framework.reverse import reverse

from letter_templates.enums import Decisions
from test_helpers.clients import DataTestClient


class DecisionsTests(DataTestClient):
    def test_get_decisions_success(self):
        url = reverse("static:decisions:decisions")

        response = self.client.get(url)
        response_data = response.json()["decisions"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(Decisions.choices))
        for decision in Decisions.choices:
            self.assertIn(decision[0], str(response_data))
