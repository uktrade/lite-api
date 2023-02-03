from uuid import uuid4

from django.urls import reverse
from faker import Faker
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import CaseAssignment
from api.cases.tests.factories import CaseAssignmentFactory
from api.queues.models import Queue
from test_helpers.clients import DataTestClient

faker = Faker()


class CaseAssignmentsTests(DataTestClient):
    def setUp(self):
        super().setUp()

        # Cases
        self.case = self.create_clc_query("Query", self.organisation)
        self.case_2 = self.create_clc_query("Query", self.organisation)
        self.case_3 = self.create_clc_query("Query", self.organisation)

        # Users
        self.gov_user = self.create_gov_user("gov1@email.com", team=self.team)
        self.gov_user_2 = self.create_gov_user(email="1@1.1", team=self.team)
        self.gov_user_3 = self.create_gov_user(email="2@2.2", team=self.team)

        self.url = reverse("queues:case_assignments", kwargs={"pk": self.queue.id})

    def test_can_assign_a_single_user_to_case_on_a_queue(self):
        data = {"case_assignments": [{"case_id": self.case.id, "users": [self.gov_user.pk]}], "note": faker.word()}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case_assignment = CaseAssignment.objects.get()
        self.assertEqual(case_assignment.case.id, self.case.id)
        self.assertEqual(case_assignment.queue.id, self.queue.id)
        self.assertEqual(case_assignment.user.pk, self.gov_user.pk)
        self.assertEqual(Audit.objects.get(verb=AuditType.ASSIGN_USER_TO_CASE).payload["additional_text"], data["note"])

    def test_can_assign_many_users_to_many_cases(self):
        data = {
            "case_assignments": [
                {
                    "case_id": self.case.id,
                    "users": [self.gov_user.pk, self.gov_user_2.pk, self.gov_user_3.pk],
                },
                {
                    "case_id": self.case_2.id,
                    "users": [self.gov_user.pk, self.gov_user_2.pk, self.gov_user_3.pk],
                },
            ]
        }

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CaseAssignment.objects.count(), 6)
        for case in [self.case, self.case_2]:
            for user in [self.gov_user, self.gov_user_2, self.gov_user_3]:
                self.assertTrue(CaseAssignment.objects.filter(case=case, user=user).exists())

    def test_all_assignments_are_cleared_when_a_case_leaves_a_queue(self):
        self.queue.cases.add(self.case)
        CaseAssignment.objects.create(queue=self.queue, case=self.case.case_ptr, user=self.gov_user)

        self.url = reverse("cases:queues", kwargs={"pk": self.case.id})

        data = {"queues": []}

        self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(len(CaseAssignment.objects.all()), 0)

    def test_assignments_persist_if_queue_is_not_removed_from_a_queue(self):
        CaseAssignment.objects.create(queue=self.queue, case=self.case, user=self.gov_user)

        self.url = reverse("cases:case", kwargs={"pk": self.case.id})

        new_queue = Queue(name="new queue", team=self.team)
        new_queue.save()

        data = {"queues": [new_queue.id, self.queue.id]}

        self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(len(CaseAssignment.objects.all()), 1)

    def test_can_see_lists_of_users_assigned_to_each_case(self):
        self.create_case_assignment(self.queue, self.case, [self.gov_user, self.gov_user_2, self.gov_user_3])
        self.create_case_assignment(self.queue, self.case_2, [self.gov_user, self.gov_user_2])

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["case_assignments"]

        extract_case_and_user_id = [{"case": item["case"], "user": item["user"]["id"]} for item in response_data]
        for user in [self.gov_user, self.gov_user_2, self.gov_user_3]:
            self.assertTrue({"case": str(self.case.pk), "user": str(user.pk)} in extract_case_and_user_id)
        for user in [self.gov_user, self.gov_user_2]:
            self.assertTrue({"case": str(self.case_2.pk), "user": str(user.pk)} in extract_case_and_user_id)

    def test_deactivated_user_is_removed_from_assignments(self):
        self.create_case_assignment(self.queue, self.case, self.gov_user)
        self.create_case_assignment(self.queue, self.case_2, [self.gov_user, self.gov_user_2])
        self.create_case_assignment(self.queue, self.case_3, self.gov_user_2)

        # Deactivate initial gov user
        data = {"status": "Deactivated"}
        url = reverse("gov_users:gov_user", kwargs={"pk": self.gov_user.pk})
        self.client.put(url, data, **self.gov_headers)

        # Ensure that the deactivated user has been removed from all cases
        self.assertEqual(self.gov_user.case_assignments.count(), 0)
        self.assertFalse(CaseAssignment.objects.filter(user=self.gov_user).exists())
        self.assertEqual(CaseAssignment.objects.filter(user=self.gov_user_2).count(), 2)


class CaseAssignmentDetailTest(DataTestClient):
    def test_delete_assignment_does_not_exist(self):

        url = reverse("queues:case_assignment_detail", kwargs={"queue_id": uuid4(), "assignment_id": uuid4()})
        response = self.client.delete(url, **self.gov_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"error": "No such case assignment"}

    def test_delete_assignment_success(self):

        assignment = CaseAssignmentFactory()
        url = reverse(
            "queues:case_assignment_detail", kwargs={"queue_id": assignment.queue.id, "assignment_id": assignment.id}
        )
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
