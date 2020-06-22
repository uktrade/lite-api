import uuid

from django.urls import reverse
from parameterized import parameterized
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from cases.enums import AdviceType, AdviceLevel, CaseTypeEnum
from cases.enums import CaseTypeSubTypeEnum
from test_helpers.clients import DataTestClient


class HMRCIntegrationUsageTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:hmrc_integration")

    def create_siel_licence(self):
        standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        return self.create_licence(standard_application, is_complete=True)

    def create_f680_licence(self):
        f680_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.F680)
        self.create_advice(self.gov_user, f680_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        return self.create_licence(f680_application, is_complete=True)

    def create_gifting_licence(self):
        gifting_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.GIFTING)
        self.create_advice(self.gov_user, gifting_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        return self.create_licence(gifting_application, is_complete=True)

    def create_exhibition_licence(self):
        exhibition_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.EXHIBITION)
        self.create_advice(self.gov_user, exhibition_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        return self.create_licence(exhibition_application, is_complete=True)

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_data_transfer_object_success(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.application.goods.first().usage

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.application.goods.first().good.id), "usage": 10}],
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertNotEqual(licence.application.goods.first().usage, original_usage)
        self.assertEqual(licence.application.goods.first().usage, 10)

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_data_transfer_object_no_licences_failure(self, create_licence):
        create_licence(self)

        response = self.client.put(self.url, {})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_data_transfer_object_no_licence_ids_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url, {"licences": [{"goods": [{"id": str(licence.application.goods.first().good.id), "usage": 10}]}]},
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_data_transfer_object_invalid_licence_id_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(uuid.uuid4()),
                        "goods": [{"id": str(licence.application.goods.first().good.id), "usage": 10}],
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_data_transfer_object_no_goods_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(self.url, {"licences": [{"id": str(licence.id)}]})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_data_transfer_object_no_good_ids_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(self.url, {"licences": [{"id": str(licence.id), "goods": [{"usage": 10}]}]})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_data_transfer_object_invalid_good_id_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url, {"licences": [{"id": str(licence.id), "goods": [{"id": str(uuid.uuid4()), "usage": 10}]}]},
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_data_transfer_object_no_good_usage_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url,
            {"licences": [{"id": str(licence.id), "goods": [{"id": str(licence.application.goods.first().good.id)}]}]},
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_data_transfer_object_open_application_failure(self):  # (has no concept of Usage)
        open_application = self.create_open_application_case(self.organisation)
        licence = self.create_licence(open_application, is_complete=True)

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.application.goods_type.first().id), "usage": 10}],
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licence"], [f"{CaseTypeSubTypeEnum.STANDARD} Licence '{licence.id}' not found."],
        )
