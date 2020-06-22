import uuid

from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from cases.enums import AdviceType, AdviceLevel
from test_helpers.clients import DataTestClient


class HMRCIntegrationSerializersTests(DataTestClient):
    url = reverse("licences:hmrc_integration")

    def test_data_transfer_object_success(self):
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

    def test_data_transfer_object_no_licences_failure(self):
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

        response = self.client.put(self.url, {})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_data_transfer_object_no_licence_ids_failure(self):
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

        response = self.client.put(
            self.url,
            {"licences": [{"goods": [{"id": str(self.standard_application.goods.first().good.id), "usage": 10}]}]},
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_data_transfer_object_invalid_licence_id_failure(self):
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(uuid.uuid4()),
                        "goods": [{"id": str(self.standard_application.goods.first().good.id), "usage": 10}],
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_data_transfer_object_no_goods_failure(self):
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

        response = self.client.put(self.url, {"licences": [{"id": str(self.standard_licence.id)}]})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_data_transfer_object_no_good_ids_failure(self):
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

        response = self.client.put(
            self.url, {"licences": [{"id": str(self.standard_licence.id), "goods": [{"usage": 10}]}]},
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_data_transfer_object_invalid_good_id_failure(self):
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

        response = self.client.put(
            self.url,
            {"licences": [{"id": str(self.standard_licence.id), "goods": [{"id": str(uuid.uuid4()), "usage": 10}]}]},
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_data_transfer_object_no_good_usage_failure(self):
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(self.standard_licence.id),
                        "goods": [{"id": str(self.standard_application.goods.first().good.id)}],
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
