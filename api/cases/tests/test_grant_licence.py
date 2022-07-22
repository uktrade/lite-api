from unittest import mock
from django.urls import reverse
from rest_framework import status

from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from api.audit_trail.models import Audit
from api.cases.enums import AdviceType, CaseTypeEnum, AdviceLevel
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.core.constants import GovPermissions
from api.core.exceptions import PermissionDeniedError
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
        self.create_advice(self.gov_user, self.standard_case, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.template = self.create_letter_template(
            name="Template",
            case_types=[CaseTypeEnum.SIEL.id],
            decisions=[Decision.objects.get(name=AdviceType.APPROVE)],
        )

    @mock.patch("api.cases.views.views.notify_exporter_licence_issued")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_grant_standard_application_success(self, send_exporter_notifications_func, mock_notify):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        licence = self.create_licence(self.standard_case, status=LicenceStatus.DRAFT)
        self.create_generated_case_document(
            self.standard_case, self.template, advice_type=AdviceType.APPROVE, licence=licence
        )

        response = self.client.put(self.url, data={}, **self.gov_headers)
        self.standard_case.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["licence"], str(licence.id))
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
        self.assertEqual(Audit.objects.count(), 4)
        send_exporter_notifications_func.assert_called()
        mock_notify.assert_called_with(licence)

    def test_grant_standard_application_wrong_permission_failure(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_CLEARANCE_FINAL_ADVICE.name])
        self.create_licence(self.standard_case, status=LicenceStatus.DRAFT)
        self.create_generated_case_document(self.standard_case, self.template, advice_type=AdviceType.APPROVE)

        response = self.client.put(self.url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"errors": {"error": PermissionDeniedError.default_detail}})

    def test_missing_advice_document_failure(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.create_licence(self.standard_case, status=LicenceStatus.DRAFT)

        response = self.client.put(self.url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"decision-approve": [Cases.Licence.MISSING_DOCUMENTS]}})

    @mock.patch("api.cases.views.views.notify_exporter_licence_issued")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_grant_clearance_success(self, send_exporter_notifications_func, mock_notify):
        clearance_case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(clearance_case)
        self.create_advice(self.gov_user, clearance_case, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.url = reverse("cases:finalise", kwargs={"pk": clearance_case.id})

        self.gov_user.role.permissions.set([GovPermissions.MANAGE_CLEARANCE_FINAL_ADVICE.name])
        licence = self.create_licence(clearance_case, status=LicenceStatus.DRAFT)
        self.create_generated_case_document(
            clearance_case, self.template, advice_type=AdviceType.APPROVE, licence=licence
        )

        response = self.client.put(self.url, data={}, **self.gov_headers)
        clearance_case.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["licence"], str(licence.id))
        self.assertEqual(
            Licence.objects.filter(
                case=clearance_case,
                status=LicenceStatus.ISSUED,
                decisions__exact=Decision.objects.get(name=AdviceType.APPROVE),
            ).count(),
            1,
        )
        self.assertEqual(clearance_case.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)
        self.assertEqual(Audit.objects.count(), 5)
        send_exporter_notifications_func.assert_called()
        mock_notify.assert_called_with(licence)

    def test_grant_clearance_wrong_permission_failure(self):
        clearance_case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(clearance_case)
        self.url = reverse("cases:finalise", kwargs={"pk": clearance_case.id})

        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.create_licence(clearance_case, status=LicenceStatus.DRAFT)
        self.create_generated_case_document(clearance_case, self.template, advice_type=AdviceType.APPROVE)

        response = self.client.put(self.url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"errors": {"error": PermissionDeniedError.default_detail}})

    def test_finalise_case_without_licence_success(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.create_generated_case_document(self.standard_case, self.template, advice_type=AdviceType.APPROVE)

        response = self.client.put(self.url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {"case": str(self.standard_case.pk)})

    @mock.patch("api.licences.helpers.notify_exporter_licence_revoked")
    @mock.patch("api.cases.views.views.notify_exporter_licence_issued")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_grant_standard_application_licence_and_revoke(
        self, send_exporter_notifications_func, mock_notify_licence_issue, mock_notify_licence_revoked
    ):
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )
        licence = self.create_licence(self.standard_case, status=LicenceStatus.DRAFT)
        self.create_generated_case_document(
            self.standard_case, self.template, advice_type=AdviceType.APPROVE, licence=licence
        )

        response = self.client.put(self.url, data={}, **self.gov_headers)
        self.standard_case.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["licence"], str(licence.id))
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
        mock_notify_licence_issue.assert_called_with(licence)

        self.change_status_url = reverse("applications:manage_status", kwargs={"pk": self.standard_case.id})
        data = {"status": CaseStatusEnum.REVOKED}
        response = self.client.put(self.change_status_url, data=data, **self.gov_headers)

        self.standard_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_case.status, get_case_status_by_status(CaseStatusEnum.REVOKED))
        mock_notify_licence_revoked.assert_called_with(licence)
