from unittest import mock
from django.urls import reverse
from rest_framework import status

from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceType, LicenceDecisionType
from api.licences.models import LicenceDecision
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.generated_documents.tests.factories import SIELLicenceDocumentFactory
from api.cases.tests.factories import FinalAdviceFactory
from api.core.constants import GovPermissions
from api.licences.tests.factories import StandardLicenceFactory
from lite_content.lite_api.strings import Cases
from api.staticdata.decisions.models import Decision
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient


class FinaliseCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_case = self.create_standard_application_case(self.organisation)
        self.url = reverse("cases:finalise", kwargs={"pk": self.standard_case.id})
        FinalAdviceFactory(user=self.gov_user, case=self.standard_case, type=AdviceType.APPROVE)

    @mock.patch("api.cases.notify.notify_exporter_licence_issued")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_grant_standard_application_success(self, send_exporter_notifications_func, mock_notify):
        licence = StandardLicenceFactory(case=self.standard_case, status=LicenceStatus.DRAFT)
        SIELLicenceDocumentFactory(case=self.standard_case, licence=licence)
        self.assertIsNone(self.standard_case.appeal_deadline)

        response = self.client.put(self.url, data={}, **self.lu_case_officer_headers)
        self.standard_case.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Licence.objects.filter(
                case=self.standard_case,
                status=LicenceStatus.ISSUED,
                decisions__exact=Decision.objects.get(name=AdviceType.APPROVE),
            ).count(),
            1,
        )
        self.assertEqual(self.standard_case.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)
        self.assertEqual(Audit.objects.count(), 6)

        self.assertTrue(
            Audit.objects.filter(
                target_object_id=self.standard_case.id,
                verb=AuditType.CREATED_FINAL_RECOMMENDATION,
                payload__decision=AdviceType.APPROVE,
            ).exists()
        )
        self.assertTrue(
            LicenceDecision.objects.filter(case=self.standard_case, decision=LicenceDecisionType.ISSUED).exists()
        )

        self.assertIsNone(self.standard_case.appeal_deadline)
        send_exporter_notifications_func.assert_called()
        mock_notify.assert_called_with(self.standard_case)

    def test_grant_standard_application_wrong_permission_failure(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_CLEARANCE_FINAL_ADVICE.name])
        StandardLicenceFactory(case=self.standard_case, status=LicenceStatus.DRAFT)
        SIELLicenceDocumentFactory(case=self.standard_case)

        response = self.client.put(self.url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"errors": {"detail": "You do not have permission to perform this action."}})

    def test_missing_advice_document_failure(self):
        StandardLicenceFactory(case=self.standard_case, status=LicenceStatus.DRAFT)

        response = self.client.put(self.url, data={}, **self.lu_case_officer_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"decision-approve": [Cases.Licence.MISSING_DOCUMENTS]}})

    def test_finalise_case_without_licence_success(self):
        SIELLicenceDocumentFactory(case=self.standard_case)

        response = self.client.put(self.url, data={}, **self.lu_case_officer_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {"case": str(self.standard_case.pk), "licence": ""})

    @mock.patch("api.licences.models.notify_exporter_licence_revoked")
    @mock.patch("api.cases.notify.notify_exporter_licence_issued")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_grant_standard_application_licence_and_revoke(
        self, send_exporter_notifications_func, mock_notify_licence_issue, mock_notify_licence_revoked
    ):
        licence = StandardLicenceFactory(case=self.standard_case, status=LicenceStatus.DRAFT)
        SIELLicenceDocumentFactory(case=self.standard_case, licence=licence)

        response = self.client.put(self.url, data={}, **self.lu_case_officer_headers)
        self.standard_case.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Licence.objects.filter(
                case=self.standard_case,
                status=LicenceStatus.ISSUED,
                decisions__exact=Decision.objects.get(name=AdviceType.APPROVE),
            ).count(),
            1,
        )
        self.assertEqual(self.standard_case.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)
        # self.assertEqual(Audit.objects.count(), 4)
        send_exporter_notifications_func.assert_called()
        mock_notify_licence_issue.assert_called_with(self.standard_case)

        self.change_status_url = reverse("caseworker_applications:change_status", kwargs={"pk": self.standard_case.id})
        data = {"status": CaseStatusEnum.REVOKED}
        response = self.client.post(self.change_status_url, data=data, **self.gov_headers)

        self.standard_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_case.status, get_case_status_by_status(CaseStatusEnum.REVOKED))
        mock_notify_licence_revoked.assert_called_with(licence)

    @mock.patch("api.licences.models.notify_exporter_licence_suspended")
    @mock.patch("api.cases.notify.notify_exporter_licence_issued")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_grant_standard_application_licence_and_suspend(
        self, send_exporter_notifications_func, mock_notify_licence_issue, mock_notify_licence_suspended
    ):
        licence = StandardLicenceFactory(case=self.standard_case, status=LicenceStatus.DRAFT)
        SIELLicenceDocumentFactory(case=self.standard_case, licence=licence)

        response = self.client.put(self.url, data={}, **self.lu_case_officer_headers)
        self.standard_case.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Licence.objects.filter(
                case=self.standard_case,
                status=LicenceStatus.ISSUED,
                decisions__exact=Decision.objects.get(name=AdviceType.APPROVE),
            ).count(),
            1,
        )
        self.assertEqual(self.standard_case.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)

        send_exporter_notifications_func.assert_called()
        mock_notify_licence_issue.assert_called_with(self.standard_case)

        self.change_status_url = reverse("caseworker_applications:change_status", kwargs={"pk": self.standard_case.id})
        data = {"status": CaseStatusEnum.SUSPENDED}
        response = self.client.post(self.change_status_url, data=data, **self.gov_headers)

        self.standard_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_case.status, get_case_status_by_status(CaseStatusEnum.SUSPENDED))
        mock_notify_licence_suspended.assert_called_with(licence)
