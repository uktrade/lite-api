from cases.enums import AdviceType, AdviceLevel
from licences.serializers.view_licence import HMRCIntegrationLicenceSerializer
from test_helpers.clients import DataTestClient


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

    def _assert_dto(self, data, licence):
        self.assertEqual(len(data), 9)
        self.assertEqual(data["id"], str(licence.id))
