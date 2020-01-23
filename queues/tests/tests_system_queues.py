from django.urls import reverse
from rest_framework import status

from audit_trail.models import Audit
from audit_trail.payload import AuditType
from cases.models import CaseAssignment
from queues.constants import (
    ALL_CASES_QUEUE_ID,
    OPEN_CASES_QUEUE_ID,
    MY_TEAMS_QUEUES_CASES_ID,
    UPDATED_CASES_QUEUE_ID,
    MY_ASSIGNED_CASES_QUEUE_ID,
    MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
)
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token
from users.models import GovUser


def _setup_common(self):
    self.queue1 = self.create_queue("queue1", self.team)
    self.queue2 = self.create_queue("queue2", self.team)

    self.case = self.create_clc_query("Query", self.organisation)
    self.case_2 = self.create_clc_query("Query", self.organisation)
    self.case_3 = self.create_clc_query("Query", self.organisation)
    self.case_3.query.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
    self.case_3.query.save()


def _create_case_and_assign_user(self):
    case_assigned_to_user = self.create_standard_application_case(self.organisation).get_case()
    case_assigned_to_user.queues.set([self.queue])
    case_assignment = CaseAssignment.objects.create(case=case_assigned_to_user, queue=self.queue)
    case_assignment.users.set([self.gov_user])
    return case_assigned_to_user


def _create_case_and_assign_user_as_case_officer(self):
    case_as_case_officer = self.create_standard_application_case(self.organisation)
    case_as_case_officer.queues.set([self.queue])
    case_as_case_officer.case_officer = self.gov_user
    case_as_case_officer.save()
    return case_as_case_officer


def _update_case(self, case):
    case.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
    case.save()
    audit = Audit.objects.create(
        actor=self.exporter_user,
        verb=AuditType.UPDATED_STATUS.value,
        target=case,
        payload={"status": CaseStatusEnum.APPLICANT_EDITING},
    )
    self.gov_user.send_notification(content_object=audit, case=case)


class AllCasesQueueTests(DataTestClient):
    def setUp(self):
        super().setUp()
        _setup_common(self)

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
