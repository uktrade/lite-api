from unittest import mock

from api.applications import notify
from api.cases.enums import AdviceLevel, AdviceType
from gov_notify.enums import TemplateType
from gov_notify.payloads import CaseWorkerCountersignCaseReturn, ExporterCaseOpenedForEditing
from test_helpers.clients import DataTestClient


class NotifyTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.standard_application.refresh_from_db()

    @mock.patch("api.applications.notify.send_email")
    def test_notify_licence_issued(self, mock_send_email):
        expected_payload = ExporterCaseOpenedForEditing(
            user_first_name=self.exporter_user.first_name,
            application_reference=self.standard_application.reference_code,
            exporter_frontend_url="https://exporter.lite.service.localhost.uktrade.digital/",
        )

        notify.notify_exporter_case_opened_for_editing(self.standard_application)

        mock_send_email.assert_called_with(
            self.exporter_user.email,
            TemplateType.EXPORTER_CASE_OPENED_FOR_EDITING,
            expected_payload,
        )

    @mock.patch("api.applications.notify.send_email")
    def test_notify_countersign_case_returned(self, mock_send_email):
        advice = self.create_advice(
            self.gov_user,
            self.standard_application,
            "good",
            AdviceType.REFUSE,
            AdviceLevel.USER,
            countersign_comments="misspelling",
            countersigned_by=self.gov_user,
        )
        caseworker_frontend_url = f"https://internal.lite.service.localhost.uktrade.digital/cases/{self.standard_application.id}/countersign-advice/"
        data = {
            "case_reference": self.standard_application.reference_code,
            "countersigner_name": f"{advice.countersigned_by.first_name} {advice.countersigned_by.last_name}",
            "countersign_comments": advice.countersign_comments,
            "recommendation_section_url": caseworker_frontend_url,
        }
        expected_payload = CaseWorkerCountersignCaseReturn(**data)
        notify.notify_caseworker_countersign_return(self.standard_application)

        mock_send_email.assert_called_with(
            self.gov_user.email,
            TemplateType.CASEWORKER_COUNTERSIGN_CASE_RETURN,
            expected_payload,
        )
