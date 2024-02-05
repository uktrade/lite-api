from django.urls import reverse
from faker import Faker
from parameterized import parameterized
from rest_framework import status

from api.applications.tests.factories import StandardApplicationFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import CaseAssignment
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import StandardLicenceFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient

faker = Faker()


class ChangeStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = StandardApplicationFactory()
        self.url = reverse("cases:case", kwargs={"pk": self.case.id})

    def test_optional_note(self):
        """
        When changing status, allow for optional notes to be added
        """

        data = {"status": CaseStatusEnum.WITHDRAWN, "note": faker.word()}

        response = self.client.patch(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Audit.objects.get(verb=AuditType.UPDATED_STATUS).payload["additional_text"], data["note"])

    @parameterized.expand(
        [
            (
                CaseStatusEnum.SUSPENDED,
                LicenceStatus.SUSPENDED,
            ),
            (
                CaseStatusEnum.SURRENDERED,
                LicenceStatus.SURRENDERED,
            ),
            (
                CaseStatusEnum.REVOKED,
                LicenceStatus.REVOKED,
            ),
        ]
    )
    def test_certain_case_statuses_changes_licence_status(self, case_status, licence_status):
        licence = StandardLicenceFactory(case=self.case, status=LicenceStatus.ISSUED)

        data = {"status": case_status}
        response = self.client.patch(self.url, data=data, **self.gov_headers)

        self.case.refresh_from_db()
        licence.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.case.status.status, case_status)
        self.assertEqual(licence.status, licence_status)


class EndUserAdvisoryUpdate(DataTestClient):
    def setUp(self):
        super().setUp()
        self.end_user_advisory = self.create_end_user_advisory_case(
            "end_user_advisory", "my reasons", organisation=self.organisation
        )
        self.url = reverse(
            "cases:case",
            kwargs={"pk": self.end_user_advisory.id},
        )

        self.end_user_advisory.case_officer = self.gov_user
        self.end_user_advisory.save()
        self.end_user_advisory.queues.set([self.queue])
        CaseAssignment.objects.create(case=self.end_user_advisory, queue=self.queue, user=self.gov_user)

    def test_update_end_user_advisory_status_to_withdrawn_success(self):
        """
        When a case is set to a the withdrawn status, its assigned users, case officer and queues should be removed
        """
        data = {"status": CaseStatusEnum.WITHDRAWN}

        response = self.client.patch(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.end_user_advisory.refresh_from_db()
        self.assertEqual(self.end_user_advisory.status.status, CaseStatusEnum.WITHDRAWN)
        self.assertEqual(self.end_user_advisory.queues.count(), 0)
        self.assertEqual(self.end_user_advisory.case_officer, None)
        self.assertEqual(CaseAssignment.objects.filter(case=self.end_user_advisory).count(), 0)


class EndUserAdvisoryStatus(DataTestClient):
    def setUp(self):
        super().setUp()
        self.query = self.create_end_user_advisory("A note", "Unsure about something", self.organisation)
        self.query.status = get_case_status_by_status(CaseStatusEnum.CLOSED)
        self.query.save()

        self.url = reverse("cases:case", kwargs={"pk": self.query.id})

    def test_gov_set_status_when_no_permission_to_reopen_closed_cases_failure(self):
        data = {"status": CaseStatusEnum.SUBMITTED}

        response = self.client.patch(self.url, data=data, **self.gov_headers)
        self.query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.query.status.status, CaseStatusEnum.CLOSED)

    def test_gov_set_status_when_they_have_permission_to_reopen_closed_cases_success(self):
        data = {"status": CaseStatusEnum.SUBMITTED}

        # Give gov user super used role, to include reopen closed cases permission
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        response = self.client.patch(self.url, data=data, **self.gov_headers)
        self.query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.query.status.status, CaseStatusEnum.SUBMITTED)


class GoodsQueryManageStatusTests(DataTestClient):
    @parameterized.expand([["create_clc_query"], ["create_pv_grading_query"]])
    def test_set_query_status_to_withdrawn_removes_case_from_queues_users_and_updates_status_success(self, cls_func):
        """
        When a case is set to a terminal status, its assigned users, case officer and queues should be removed
        """
        query = getattr(self, cls_func)("This is a widget", self.organisation)
        query.case_officer = self.gov_user
        query.save()
        query.queues.set([self.queue])
        CaseAssignment.objects.create(case=query, queue=self.queue, user=self.gov_user)
        url = reverse("cases:case", kwargs={"pk": query.pk})
        data = {"status": "withdrawn"}

        response = self.client.patch(url, data, **self.gov_headers)
        query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(query.status.status, CaseStatusEnum.WITHDRAWN)
        self.assertEqual(query.queues.count(), 0)
        self.assertEqual(query.case_officer, None)
        self.assertEqual(CaseAssignment.objects.filter(case=query).count(), 0)

    def test_case_routing_automation_status_change(self):
        query = self.create_goods_query("This is a widget", self.organisation, "reason", "reason")
        query.queues.set([self.queue])

        routing_queue = self.create_queue("new queue", self.team)
        self.create_routing_rule(
            self.team.id,
            routing_queue.id,
            3,
            status_id=get_case_status_by_status(CaseStatusEnum.PV).id,
            additional_rules=[],
        )
        self.assertNotEqual(query.status.status, CaseStatusEnum.PV)

        url = reverse("cases:case", kwargs={"pk": query.pk})
        data = {"status": CaseStatusEnum.PV}

        response = self.client.patch(url, data, **self.gov_headers)
        query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(query.status.status, CaseStatusEnum.PV)
        self.assertEqual(query.queues.count(), 1)
        self.assertEqual(query.queues.first().id, routing_queue.id)
