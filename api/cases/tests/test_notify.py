from unittest import mock

from api.cases import notify
from api.licences.tests.factories import LicenceFactory
from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterLicenceIssued
from test_helpers.clients import DataTestClient


class NotifyTests(DataTestClient):
    def setUp(self):
        super().setUp()
        case = self.create_standard_application_case(self.organisation)
        self.licence = LicenceFactory(case=case)

    @mock.patch("api.cases.notify.send_email")
    def test_notify_licence_issued(self, mock_send_email):
        expected_payload = ExporterLicenceIssued(
            user_first_name=self.exporter_user.first_name,
            application_reference=self.licence.case.reference_code,
            exporter_frontend_url="https://exporter.lite.service.localhost.uktrade.digital/",
        )

        notify.notify_exporter_licence_issued(self.licence)

        mock_send_email.assert_called_with(
            self.exporter_user.email,
            TemplateType.EXPORTER_LICENCE_ISSUED,
            expected_payload,
        )
