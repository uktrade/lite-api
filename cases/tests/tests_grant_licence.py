from unittest import mock

from django.urls import reverse
from rest_framework import status

from licences.models import Licence
from audit_trail.models import Audit
from cases.enums import AdviceType, CaseTypeEnum
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import FinalAdvice
from conf.constants import GovPermissions
from conf.exceptions import PermissionDeniedError
from lite_content.lite_api.strings import Cases
from static.decisions.models import Decision
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient


class FinaliseCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_case = self.create_standard_application_case(self.organisation)
        self.url = reverse("cases:finalise", kwargs={"pk": self.standard_case.id})
        self.create_advice(self.gov_user, self.standard_case, "good", AdviceType.APPROVE, FinalAdvice)
        self.template = self.create_letter_template(
            name="Template",
            case_types=[CaseTypeEnum.SIEL.id],
            decisions=[Decision.objects.get(name=AdviceType.APPROVE)],
        )

    @mock.patch("cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_grant_standard_application_success(self, send_exporter_notifications_func):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        licence = self.create_licence(self.standard_case, is_complete=False)
        self.create_generated_case_document(self.standard_case, self.template, advice_type=AdviceType.APPROVE)

        response = self.client.put(self.url, data={}, **self.gov_headers)
        self.standard_case.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["licence"], str(licence.id))
        self.assertEqual(Licence.objects.filter(application=self.standard_case, is_complete=True).count(), 1)
        self.assertEqual(self.standard_case.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)
        self.assertEqual(Audit.objects.count(), 1)
        send_exporter_notifications_func.assert_called()

    def test_grant_standard_application_wrong_permission_failure(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_CLEARANCE_FINAL_ADVICE.name])
        self.create_licence(self.standard_case, is_complete=False)
        self.create_generated_case_document(self.standard_case, self.template, advice_type=AdviceType.APPROVE)

        response = self.client.put(self.url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"errors": {"error": PermissionDeniedError.default_detail}})

    def test_missing_advice_document_failure(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.create_licence(self.standard_case, is_complete=False)

        response = self.client.put(self.url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": [Cases.Licence.MISSING_DOCUMENTS]})

    @mock.patch("cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_grant_clearance_success(self, send_exporter_notifications_func):
        clearance_case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(clearance_case)
        self.url = reverse("cases:finalise", kwargs={"pk": clearance_case.id})

        self.gov_user.role.permissions.set([GovPermissions.MANAGE_CLEARANCE_FINAL_ADVICE.name])
        licence = self.create_licence(clearance_case, is_complete=False)
        self.create_generated_case_document(clearance_case, self.template, advice_type=AdviceType.APPROVE)

        response = self.client.put(self.url, data={}, **self.gov_headers)
        clearance_case.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["licence"], str(licence.id))
        self.assertEqual(Licence.objects.filter(application=clearance_case, is_complete=True).count(), 1)
        self.assertEqual(clearance_case.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)
        self.assertEqual(Audit.objects.count(), 1)
        send_exporter_notifications_func.assert_called()

    def test_grant_clearance_wrong_permission_failure(self):
        clearance_case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(clearance_case)
        self.url = reverse("cases:finalise", kwargs={"pk": clearance_case.id})

        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.create_licence(clearance_case, is_complete=False)
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
