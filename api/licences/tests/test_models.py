from test_helpers.clients import DataTestClient
from api.licences.tests.factories import StandardLicenceFactory
from api.licences.enums import LicenceStatus, licence_status_to_hmrc_integration_action


class LicenceStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)

    def test_suspend_licence_cancel_message_not_sent_to_hmrc(self):
        licence = StandardLicenceFactory(case=self.standard_application, status=LicenceStatus.ISSUED)
        licence.suspend()

        assert licence.status == LicenceStatus.SUSPENDED
        assert licence_status_to_hmrc_integration_action.get(licence.status) == None
