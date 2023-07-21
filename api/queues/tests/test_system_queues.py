from django.urls import reverse
from rest_framework import status

from api.cases.models import CaseAssignment
from api.queues.constants import OPEN_CASES_QUEUE_ID
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class AllCasesQueueTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.queue1 = self.create_queue("queue1", self.team)
        self.queue2 = self.create_queue("queue2", self.team)

        # Cases
        standard_application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(standard_application)
        standard_application_2 = self.create_draft_standard_application(self.organisation)
        self.case_2 = self.submit_application(standard_application_2)
        standard_application_3 = self.create_draft_standard_application(self.organisation)
        self.case_3 = self.submit_application(standard_application_3)
        self.case_3.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.case_3.save()

    def test_get_user_case_assignments_returns_expected_cases(self):
        """
        Given Cases assigned to various queues
        When a user requests the All Cases system queue
        Then all cases are returned regardless of the queues they are assigned to
        """
        CaseAssignment.objects.create(queue=self.queue1, case=self.case, user=self.gov_user)
        CaseAssignment.objects.create(queue=self.queue2, case=self.case_2, user=self.gov_user)

        url = reverse("queues:case_assignments", kwargs={"pk": OPEN_CASES_QUEUE_ID})

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response_data["case_assignments"]))

        case_id_list = [c["case"] for c in response_data["case_assignments"]]

        self.assertTrue(str(self.case.id) in case_id_list)
        self.assertTrue(str(self.case_2.id) in case_id_list)
