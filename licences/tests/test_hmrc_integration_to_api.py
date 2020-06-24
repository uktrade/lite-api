import uuid

from django.urls import reverse
from parameterized import parameterized
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from cases.enums import AdviceType, AdviceLevel, CaseTypeEnum
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
    def test_update_usages_success(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.application.goods.first().usage
        usage_update = 10

        response = self.client.put(
            self.url,
            {
                "transaction_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.application.goods.first().good.id), "usage": usage_update}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(licence.application.goods.first().usage, original_usage + usage_update)
        self.assertTrue(
            licence.hmrc_integration_usage_updates.filter(id="00000000-0000-0000-0000-000000000001").exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_transaction_already_exists_success(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.application.goods.first().usage
        usage_update = 10

        self.client.put(
            self.url,
            {
                "transaction_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.application.goods.first().good.id), "usage": usage_update}],
                    }
                ],
            },
        )
        response = self.client.put(
            self.url,
            {
                "transaction_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.application.goods.first().good.id), "usage": usage_update}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(licence.application.goods.first().usage, original_usage + usage_update)
        self.assertTrue(
            licence.hmrc_integration_usage_updates.filter(id="00000000-0000-0000-0000-000000000001").exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_transaction_id_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.application.goods.first().good.id), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["transaction_id"], ["This field is required."],
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_licences_failure(self, create_licence):
        create_licence(self)

        response = self.client.put(self.url, {})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"], ["This field is required."],
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_licence_ids_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url,
            {
                "transaction_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "licences": [{"goods": [{"id": str(licence.application.goods.first().good.id), "usage": 10}]}],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"], [{"id": ["This field is required."]}],
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_licence_id_failure(self, create_licence):
        licence = create_licence(self)
        invalid_licence_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "transaction_id": 1,
                "licences": [
                    {
                        "id": invalid_licence_id,
                        "goods": [{"id": str(licence.application.goods.first().good.id), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"], [f"Licence '{invalid_licence_id}' not found."],
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_goods_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url,
            {
                "transaction_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "licences": [{"id": str(licence.id)}],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"], [{"goods": ["This field is required."]}],
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_good_ids_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url,
            {
                "transaction_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "licences": [{"id": str(licence.id), "goods": [{"usage": 10}]}],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"]["licences"], [{"goods": [{"id": ["This field is required."]}]}])

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_good_id_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url,
            {
                "transaction_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "licences": [{"id": str(licence.id), "good": [{"id": str(uuid.uuid4()), "usage": 10}]}],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"], [{"goods": ["This field is required."]}],
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_good_usage_failure(self, create_licence):
        licence = create_licence(self)

        response = self.client.put(
            self.url,
            {
                "transaction_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "licences": [
                    {"id": str(licence.id), "goods": [{"id": str(licence.application.goods.first().good.id)}]}
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"], [{"goods": [{"usage": ["This field is required."]}]}],
        )

    def test_update_usages_open_application_failure(self):  # (has no concept of Usage)
        open_application = self.create_open_application_case(self.organisation)
        licence = self.create_licence(open_application, is_complete=True)

        response = self.client.put(
            self.url,
            {
                "transaction_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.application.goods_type.first().id), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"],
            [f"Licence type '{licence.application.case_type.reference}' cannot be updated; Licence '{licence.id}'."],
        )
