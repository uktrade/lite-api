from django.urls import reverse
from rest_framework import status

from cases.models import CaseAssignment
from queues.constants import OPEN_CASES_QUEUE_ID
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class AllCasesQueueTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.queue1 = self.create_queue("queue1", self.team)
        self.queue2 = self.create_queue("queue2", self.team)

        self.case = self.create_clc_query("Query", self.organisation)
        self.case_2 = self.create_clc_query("Query", self.organisation)
        self.case_3 = self.create_clc_query("Query", self.organisation)
        self.case_3.query.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.case_3.query.save()

    def test_get_user_case_assignments_returns_expected_cases(self):
        """
        Given Cases assigned to various queues
        When a user requests the All Cases system queue
        Then all cases are returned regardless of the queues they are assigned to
        """
        case_assignment = CaseAssignment(queue=self.queue1, case=self.case)
        case_assignment.save()
        case_assignment = CaseAssignment(queue=self.queue2, case=self.case_2)
        case_assignment.save()

        url = reverse("queues:case_assignments", kwargs={"pk": OPEN_CASES_QUEUE_ID})

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response_data["case_assignments"]))

        case_id_list = [c["case"] for c in response_data["case_assignments"]]

        self.assertTrue(str(self.case.id) in case_id_list)
        self.assertTrue(str(self.case_2.id) in case_id_list)
