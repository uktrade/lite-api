from unittest import mock

from api.applications import notify
from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterCaseOpenedForEditing
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
