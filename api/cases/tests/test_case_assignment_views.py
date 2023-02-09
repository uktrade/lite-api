from uuid import uuid4

from django.urls import reverse
from rest_framework import status
from parameterized import parameterized

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.tests.factories import CaseAssignmentFactory, CaseFactory
from api.cases.models import CaseAssignment
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient


class CaseAssignmentDetailTest(DataTestClient):
    def test_delete_assignment_does_not_exist(self):

        url = reverse("cases:case_assignment_detail", kwargs={"case_id": uuid4(), "assignment_id": uuid4()})
        response = self.client.delete(url, **self.gov_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"error": "No such case assignment"}

    @parameterized.expand(
        [
            ("Joe", "Bloggs", "Joe Bloggs"),
            ("", "Bloggs", "example@example.net"),
            ("", "", "example@example.net"),
        ]
    )
    def test_delete_assignment_success(self, first_name, last_name, expected_identifier):
        case = CaseFactory(status=CaseStatus.objects.get(status="submitted"))
        assignment = CaseAssignmentFactory(case=case)
        assignment.user.baseuser_ptr.first_name = first_name
        assignment.user.baseuser_ptr.last_name = last_name
        assignment.user.baseuser_ptr.email = "example@example.net"
        assignment.user.baseuser_ptr.save()
        url = reverse("cases:case_assignment_detail", kwargs={"case_id": case.id, "assignment_id": assignment.id})
        response = self.client.delete(url, **self.gov_headers)
        assert response.status_code == status.HTTP_200_OK
        expected_response = {
            "case": str(assignment.case_id),
            "id": str(assignment.id),
            "queue": str(assignment.queue_id),
            "user": {
                "email": assignment.user.email,
                "first_name": assignment.user.first_name,
                "id": str(assignment.user.baseuser_ptr.id),
                "last_name": assignment.user.last_name,
                "team": assignment.user.team.name,
            },
        }
        assert response.json() == expected_response
        assert not CaseAssignment.objects.filter(id=assignment.id).exists()

        # Ensure removal audit entry was added
        audit_entry = Audit.objects.get(verb=AuditType.REMOVE_USER_FROM_CASE)
        assert audit_entry.actor == self.gov_user
        assert audit_entry.target == assignment.case
        assert audit_entry.payload == {
            "removed_user_queue_id": str(assignment.queue.id),
            "removed_user_queue_name": assignment.queue.name,
            "removed_user_id": str(assignment.user.baseuser_ptr.id),
            "removed_user_name": expected_identifier,
        }
