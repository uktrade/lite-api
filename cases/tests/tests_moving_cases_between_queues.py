import json
from unittest import mock

from actstream.models import Action
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from audit_trail.constants import Verb, AuditType
from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity
from test_helpers.clients import DataTestClient


class MoveCasesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_clc_query("Query", self.organisation).case.get()
        self.url = reverse("cases:case", kwargs={"pk": self.case.id})
        self.queues = [
            self.create_queue("Queue 1", self.team),
            self.create_queue("Queue 2", self.team),
            self.create_queue("Queue 3", self.team),
        ]

    def test_move_case_successful(self):
        data = {"queues": [queue.id for queue in self.queues]}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(self.case.queues.values_list("id", flat=True)), set(data["queues"]))

    def test_add_and_remove_case_to_queue(self):
        queues_data = {"queues": [queue.id for queue in self.queues]}

        response = self.client.put(self.url, data=queues_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(self.case.queues.values_list("id", flat=True)), set(queues_data["queues"]),
        )

        no_queues_data = {"queues": []}

        response = self.client.put(self.url, data=no_queues_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(self.case.queues.values_list("id", flat=True)), set(no_queues_data["queues"]),
        )

    @mock.patch('audit_trail.service.create')
    def test_case_activity_created(self, mock_create):
        self.assertEqual(mock_create.call_count, 0)

        queues_data = {"queues": [str(queue.id) for queue in self.queues]}
        expected_action_payload = {"queues": sorted([queue.name for queue in self.queues])}

        self.client.put(self.url, data=queues_data, **self.gov_headers)

        self.assertEqual(mock_create.call_count, 1)

        mock_create.assert_called_once_with(
            audit_type=AuditType.CASE,
            actor=self.gov_user,
            verb=Verb.ADDED_QUEUES,
            target=self.case,
            payload=expected_action_payload
        )

        queues_data_rm = {"queues": []}

        self.client.put(self.url, data=queues_data_rm, **self.gov_headers)

        mock_create.assert_called_with(
            audit_type=AuditType.CASE,
            actor=self.gov_user,
            verb=Verb.REMOVED_QUEUES,
            target=self.case,
            payload=expected_action_payload
        )

    @parameterized.expand(
        [
            # Invalid Queues
            [{"queues": "Not an array"}],
            [{"queues": ["00000000-0000-0000-0000-000000000002"]}],
            [{"queues": ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002",]}],
        ]
    )
    def test_move_case_failure(self, data):
        existing_queues = set(self.case.queues.values_list("id", flat=True))

        response = self.client.put(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(self.case.queues.values_list("id", flat=True)), existing_queues)
