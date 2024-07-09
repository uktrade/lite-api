from django.utils import timezone
from test_helpers.clients import DataTestClient
from api.licences.models import Licence
from api.licences.enums import LicenceStatus, HMRCIntegrationActionEnum, licence_status_to_hmrc_integration_action


class LicenceStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)

    def test_suspend_licence_cancel_message_not_sent_to_hmrc(self):

        licence = Licence.objects.create(
            case=self.standard_application,
            status=LicenceStatus.ISSUED,
            reference_code="GBSIEL/2024/0000001/P",
            start_date=timezone.now().date(),
            duration=10,
        )

        licence.suspend()

        assert licence.status == LicenceStatus.SUSPENDED
        assert licence_status_to_hmrc_integration_action.get(licence.status) != HMRCIntegrationActionEnum.CANCEL
