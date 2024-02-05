from unittest import mock
from django.urls import reverse
from rest_framework import status

from api.audit_trail.models import Audit
from api.cases.enums import AdviceType, CaseTypeEnum
from api.cases.tests.factories import FinalAdviceFactory
from api.cases.libraries.get_case import get_case
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.core.constants import GovPermissions
from api.staticdata.decisions.models import Decision
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient


class RefuseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)
        self.url = reverse("cases:finalise", kwargs={"pk": self.application.id})
        FinalAdviceFactory(user=self.gov_user, case=self.application, type=AdviceType.REFUSE)
        self.template = self.create_letter_template(
            name="Template",
            case_types=[CaseTypeEnum.SIEL.id],
            decisions=[Decision.objects.get(name=AdviceType.REFUSE)],
        )

    @mock.patch("api.cases.views.views.notify_exporter_licence_refused")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_refuse_standard_application_success(self, send_exporter_notifications_func, mock_notify):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.create_generated_case_document(self.application, self.template, advice_type=AdviceType.REFUSE)

        response = self.client.put(self.url, data={}, **self.gov_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.application.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)

        # Confirm finalisation can succeed with only a refuse doc
        case_documents_query = GeneratedCaseDocument.objects.filter(case=self.application.id)
        self.assertEqual(case_documents_query.count(), 1)
        self.assertEqual(case_documents_query[0].advice_type, "refuse")
        self.assertEqual(Audit.objects.count(), 4)
        case = get_case(self.application.id)
        mock_notify.assert_called_with(case)
        send_exporter_notifications_func.assert_called()
        assert case.sub_status.name == "Refused"

    @mock.patch("api.cases.views.views.notify_exporter_licence_refused")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_refuse_standard_application_success_inform_letter_feature_letter_on(
        self, send_exporter_notifications_func, mock_notify
    ):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.create_generated_case_document(self.application, self.template, advice_type=AdviceType.REFUSE)

        response = self.client.put(self.url, data={}, **self.gov_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.application.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)
        # Confirm finalisation can succeed with only a refuse doc
        case_documents_query = GeneratedCaseDocument.objects.filter(case=self.application.id)
        self.assertEqual(case_documents_query.count(), 1)
        self.assertEqual(case_documents_query[0].advice_type, "refuse")
        self.assertEqual(Audit.objects.count(), 4)
        case = get_case(self.application.id)
        mock_notify.assert_called_with(case)
        send_exporter_notifications_func.assert_called()
        assert case.sub_status.name == "Refused"


class NLRAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)
        self.url = reverse("cases:finalise", kwargs={"pk": self.application.id})
        FinalAdviceFactory(user=self.gov_user, case=self.application, type=AdviceType.NO_LICENCE_REQUIRED)
        self.template = self.create_letter_template(
            name="Template",
            case_types=[CaseTypeEnum.SIEL.id],
            decisions=[Decision.objects.get(name=AdviceType.NO_LICENCE_REQUIRED)],
        )

    @mock.patch("api.cases.views.views.notify_exporter_licence_issued")
    @mock.patch("api.cases.views.views.notify_exporter_no_licence_required")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_no_licence_required_standard_application_success(
        self,
        send_exporter_notifications_func,
        mock_notify_exporter_no_licence_required,
        mock_notify_exporter_licence_issued,
    ):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.create_generated_case_document(self.application, self.template, advice_type=AdviceType.NO_LICENCE_REQUIRED)

        response = self.client.put(self.url, data={}, **self.gov_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.application.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)

        self.assertEqual(Audit.objects.count(), 3)
        case = get_case(self.application.id)
        mock_notify_exporter_no_licence_required.assert_called_with(case)
        mock_notify_exporter_licence_issued.assert_not_called()
        send_exporter_notifications_func.assert_called()

        assert case.sub_status == None


class ApproveAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)
        self.url = reverse("cases:finalise", kwargs={"pk": self.application.id})
        FinalAdviceFactory(user=self.gov_user, case=self.application, type=AdviceType.APPROVE)
        self.template = self.create_letter_template(
            name="Template",
            case_types=[CaseTypeEnum.SIEL.id],
            decisions=[Decision.objects.get(name=AdviceType.NO_LICENCE_REQUIRED)],
        )

    @mock.patch("api.cases.views.views.notify_exporter_licence_issued")
    @mock.patch("api.cases.generated_documents.models.GeneratedCaseDocument.send_exporter_notifications")
    def test_approve_standard_application_success(
        self,
        send_exporter_notifications_func,
        mock_notify_exporter_licence_issued,
    ):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.create_generated_case_document(self.application, self.template, advice_type=AdviceType.APPROVE)

        response = self.client.put(self.url, data={}, **self.gov_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.application.status, CaseStatus.objects.get(status=CaseStatusEnum.FINALISED))
        for document in GeneratedCaseDocument.objects.filter(advice_type__isnull=False):
            self.assertTrue(document.visible_to_exporter)

        case = get_case(self.application.id)
        send_exporter_notifications_func.assert_called()

        assert case.sub_status.name == "Approved"
