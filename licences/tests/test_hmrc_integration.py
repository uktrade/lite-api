from unittest import mock

from cases.enums import AdviceType, AdviceLevel
from licences.libraries.hmrc_integration_operations import send_licence, HMRCIntegrationException
from licences.serializers.view_licence import HMRCIntegrationLicenceSerializer
from test_helpers.clients import DataTestClient


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class HMRCIntegrationTests(DataTestClient):
    def test_data_transfer_object_standard_application(self):
        standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        standard_licence = self.create_licence(standard_application, is_complete=True)

        data = HMRCIntegrationLicenceSerializer(standard_licence).data

        self._assert_dto(data, standard_licence)

    def test_data_transfer_object_open_application(self):
        open_application = self.create_open_application_case(self.organisation)
        self.create_advice(self.gov_user, open_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        open_licence = self.create_licence(open_application, is_complete=True)

        data = HMRCIntegrationLicenceSerializer(open_licence).data

        self._assert_dto(data, open_licence)

    @mock.patch("licences.libraries.hmrc_integration_operations.post")
    def test_send_licence_success(self, requests):
        requests.return_value = MockResponse("", 201)

        standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        standard_licence = self.create_licence(standard_application, is_complete=True)

        send_licence(standard_licence)

        requests.assert_called_once()

    @mock.patch("licences.libraries.hmrc_integration_operations.post")
    def test_send_licence_failure(self, requests):
        requests.return_value = MockResponse("", 400)

        standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        standard_licence = self.create_licence(standard_application, is_complete=True)

        with self.assertRaises(HMRCIntegrationException) as exc:
            send_licence(standard_licence)

        requests.assert_called_once()

    def _assert_dto(self, data, licence):
        self.assertEqual(len(data), 9)
        self.assertEqual(data["id"], str(licence.id))
