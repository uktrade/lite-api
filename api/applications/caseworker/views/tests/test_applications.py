from parameterized import parameterized

from django.urls import reverse
from rest_framework import status

from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.applications.tests.factories import StandardApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

from test_helpers.clients import DataTestClient


class TestChangeStatus(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory(organisation=self.organisation)
        self.url = reverse(
            "caseworker_applications:change_status",
            kwargs={
                "pk": str(self.application.pk),
            },
        )

    @parameterized.expand(
        list(set(CaseStatusEnum.caseworker_operable_statuses()) - set(CaseStatusEnum.terminal_statuses()))
    )
    def test_change_status_success(self, case_status):
        self.application.status = CaseStatus.objects.get(status=case_status)
        self.application.save()
        response = self.client.post(self.url, **self.gov_headers, data={"status": CaseStatusEnum.SUBMITTED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application_id = response.json().get("id")
        self.assertEqual(application_id, str(self.application.id))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.SUBMITTED)

    def test_change_status_success_with_note(self):
        self.application.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        self.application.save()
        response = self.client.post(
            self.url, **self.gov_headers, data={"status": CaseStatusEnum.INITIAL_CHECKS, "note": "some reason"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application_id = response.json().get("id")
        self.assertEqual(application_id, str(self.application.id))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.INITIAL_CHECKS)
        audit_entry = Audit.objects.get(verb=AuditType.UPDATED_STATUS)
        assert audit_entry.payload == {
            "additional_text": "some reason",
            "status": {
                "new": CaseStatusEnum.INITIAL_CHECKS,
                "old": CaseStatusEnum.SUBMITTED,
            },
        }

    def test_change_status_not_permitted_status(self):
        self.application.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        self.application.save()
        response = self.client.post(self.url, **self.gov_headers, data={"status": CaseStatusEnum.APPLICANT_EDITING})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.SUBMITTED)

    def test_change_status_not_caseworker_operable(self):
        self.application.status = CaseStatus.objects.get(status=CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT)
        self.application.save()
        response = self.client.post(self.url, **self.gov_headers, data={"status": CaseStatusEnum.OGD_ADVICE})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT)

    def test_change_status_application_not_found(self):
        self.application.delete()
        response = self.client.post(self.url, **self.gov_headers, data={"status": CaseStatusEnum.APPLICANT_EDITING})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_status_exporter_not_permitted(self):
        self.application.organisation = self.exporter_user.organisation
        self.application.save()

        response = self.client.post(self.url, **self.exporter_headers, data={"status": CaseStatusEnum.SUBMITTED})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
