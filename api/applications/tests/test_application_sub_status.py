import uuid

from django.urls import reverse
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer

from rest_framework import status

from test_helpers.clients import DataTestClient

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.factories import CaseStatusFactory
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.statuses.models import CaseStatus, CaseSubStatus


class ApplicationManageStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.status = CaseStatus.objects.get(status="under_final_review")
        self.standard_application.status = self.status
        self.standard_application.save()
        self.url = reverse("applications:manage_sub_status", kwargs={"pk": self.standard_application.id})

    def test_gov_set_application_sub_status(self):
        self.assertIsNone(self.standard_application.sub_status)

        sub_status = CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=self.status,
        )

        data = {"sub_status": str(sub_status.pk)}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.standard_application.sub_status,
            sub_status,
        )

        # Check add audit
        audit = Audit.objects.filter(verb=AuditType.UPDATED_SUB_STATUS).order_by("-created_at")[0]
        self.assertEqual(
            audit.payload,
            {"status": "Under final review", "sub_status": "test_sub_status"},
        )

    def test_gov_set_application_sub_status_none_check_audit(self):

        data = {"sub_status": ""}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        # Check add audit
        audit = Audit.objects.filter(verb=AuditType.UPDATED_SUB_STATUS).order_by("-created_at")[0]
        self.assertEqual(
            audit.payload,
            {"status": "Under final review", "sub_status": "none"},
        )
        audit_text = AuditSerializer(audit).data["text"]
        self.assertEqual(audit_text, "updated the status to Under final review - none")

    def test_exporter_set_application_sub_status(self):
        self.assertIsNone(self.standard_application.sub_status)

        sub_status = CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=self.status,
        )

        data = {"sub_status": str(sub_status.pk)}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(self.standard_application.sub_status)

    def test_set_invalid_sub_status_pk(self):
        self.assertIsNone(self.standard_application.sub_status)

        data = {"sub_status": str(uuid.uuid4())}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(self.standard_application.sub_status)

    def test_set_sub_status_of_different_parent_status(self):
        self.assertIsNone(self.standard_application.sub_status)

        CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=self.status,
        )
        other_sub_status = CaseSubStatus.objects.create(
            name="other_test_sub_status", parent_status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )

        data = {"sub_status": str(other_sub_status.pk)}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(self.standard_application.sub_status)

    def test_set_sub_status_being_set_to_none(self):
        self.assertIsNone(self.standard_application.sub_status)

        sub_status = CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=self.status,
        )
        self.standard_application.sub_status = sub_status
        self.standard_application.save()

        data = {"sub_status": None}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(self.standard_application.sub_status)


class ApplicationSubStatusesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.status = CaseStatus.objects.get(status="final_review_second_countersign")
        self.standard_application.status = self.status
        self.standard_application.save()
        self.url = reverse("applications:application_sub_statuses", kwargs={"pk": self.standard_application.id})

    def test_get_sub_statuses(self):

        test_sub_status = CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=self.status,
            order=1,
        )
        another_test_sub_status = CaseSubStatus.objects.create(
            name="another_test_sub_status",
            parent_status=self.status,  # Order defaults to 100, so expect this last
        )
        CaseSubStatus.objects.create(
            name="other_test_sub_status",
            parent_status=CaseStatus.objects.get(status="under_final_review"),
        )
        lowest_order_sub_status = CaseSubStatus.objects.create(
            name="lowest_order_sub_status",
            parent_status=self.status,
            order=0,
        )

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {"id": str(lowest_order_sub_status.pk), "name": "lowest_order_sub_status"},
                {"id": str(test_sub_status.pk), "name": "test_sub_status"},
                {"id": str(another_test_sub_status.pk), "name": "another_test_sub_status"},
            ],
        )

    def test_get_sub_statuses_invalid_application_pk(self):
        url = reverse("applications:application_sub_statuses", kwargs={"pk": uuid.uuid4()})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
