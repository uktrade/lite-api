from unittest import mock

from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from cases.enums import AdviceType, AdviceLevel
from test_helpers.clients import DataTestClient


@mock.patch("cases.app.LITE_HMRC_INTEGRATION_ENABLED", False)  # Disable task from being run on app initialization
class HMRCIntegrationSerializersTests(DataTestClient):
    url = reverse("licences:hmrc_integration")

    def test_data_transfer_object(self):
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)
        original_usage = self.standard_application.goods.first().usage

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(self.standard_licence.id),
                        "goods": [{"id": str(self.standard_application.goods.first().good.id), "usage": 10}],
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertNotEqual(self.standard_application.goods.first().usage, original_usage)
        self.assertEqual(self.standard_application.goods.first().usage, 10)
