import uuid

from django.urls import reverse
from parameterized import parameterized
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_207_MULTI_STATUS, HTTP_208_ALREADY_REPORTED

from cases.enums import AdviceType, AdviceLevel, CaseTypeEnum
from licences.models import HMRCIntegrationUsageUpdate
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
    def test_update_usages_accepted(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.application.goods.first().usage
        transaction_id = str(uuid.uuid4())
        usage_update = 10
        licence_update = {
            "id": str(licence.id),
            "goods": [{"id": str(licence.application.goods.first().good.id), "usage": usage_update}],
        }

        response = self.client.put(self.url, {"transaction_id": transaction_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(licence.application.goods.first().usage, original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id, licences=licence).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_transaction_already_exists_already_reported(self, create_licence):
        licence = create_licence(self)
        transaction_id = str(uuid.uuid4())
        usage_update = 10
        licence_update = {
            "id": str(licence.id),
            "goods": [{"id": str(licence.application.goods.first().good.id), "usage": usage_update}],
        }
        self.client.put(self.url, {"transaction_id": transaction_id, "licences": [licence_update]})
        original_usage = licence.application.goods.first().usage

        response = self.client.put(self.url, {"transaction_id": transaction_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_208_ALREADY_REPORTED)
        self.assertEqual(licence.application.goods.first().usage, original_usage)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_accepted_and_rejected(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.application.goods.first().usage
        transaction_id = str(uuid.uuid4())
        usage_update = 10
        invalid_licence_id = str(uuid.uuid4())
        licence_updates = [
            {
                "id": str(licence.id),
                "goods": [{"id": str(licence.application.goods.first().good.id), "usage": usage_update}],
            },
            {
                "id": invalid_licence_id,
                "goods": [{"id": str(licence.application.goods.first().good.id), "usage": usage_update}],
            },
        ]

        response = self.client.put(self.url, {"transaction_id": transaction_id, "licences": licence_updates})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_updates[0]],
        )
        self.assertEqual(response.json()["licences"]["rejected"][0]["errors"], {"id": ["Licence not found."]})
        self.assertEqual(licence.application.goods.first().usage, original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id, licences=licence).exists())
        self.assertFalse(
            HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id, licences=invalid_licence_id).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_transaction_id_rejected(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.application.goods.first().usage
        usage_update = 10

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.application.goods.first().good.id), "usage": usage_update}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["transaction_id"], ["This field is required."],
        )
        self.assertEqual(licence.application.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(licences=licence).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_licences_rejected(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.application.goods.first().usage
        transaction_id = str(uuid.uuid4())

        response = self.client.put(self.url, {"transaction_id": transaction_id})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"], ["This field is required."],
        )
        self.assertEqual(licence.application.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_licence_ids_rejected(self, create_licence):
        licence = create_licence(self)
        transaction_id = str(uuid.uuid4())
        usage_update = 10
        licence_update = {"goods": [{"id": str(licence.application.goods.first().good.id), "usage": usage_update}]}

        response = self.client.put(self.url, {"transaction_id": transaction_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"id": ["This field is required."]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_licence_id_rejected(self, create_licence):
        licence = create_licence(self)
        transaction_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "transaction_id": transaction_id,
                "licences": [
                    {
                        "id": str(uuid.uuid4()),
                        "goods": [{"id": str(licence.application.goods.first().good.id), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"id": ["Licence not found."]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_goods_rejected(self, create_licence):
        licence = create_licence(self)
        transaction_id = str(uuid.uuid4())

        response = self.client.put(self.url, {"transaction_id": transaction_id, "licences": [{"id": str(licence.id)}]})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"goods": ["This field is required."]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_good_ids_rejected(self, create_licence):
        licence = create_licence(self)
        transaction_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {"transaction_id": transaction_id, "licences": [{"id": str(licence.id), "goods": [{"usage": 10}]}]},
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"goods": [{"id": ["This field is required."]}]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_good_id_rejected(self, create_licence):
        licence = create_licence(self)
        transaction_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "transaction_id": transaction_id,
                "licences": [{"id": str(licence.id), "goods": [{"id": str(uuid.uuid4()), "usage": 10}]}],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"goods": [{"id": ["Good not found on Licence."]}]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_good_usage_rejected(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.application.goods.first().usage
        transaction_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "transaction_id": transaction_id,
                "licences": [
                    {"id": str(licence.id), "goods": [{"id": str(licence.application.goods.first().good.id)}]}
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"goods": [{"usage": ["This field is required."]}]},
        )
        self.assertEqual(licence.application.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists())

    def test_update_usages_open_application_rejected(self):  # (has no concept of Usage)
        open_application = self.create_open_application_case(self.organisation)
        licence = self.create_licence(open_application, is_complete=True)
        transaction_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "transaction_id": transaction_id,
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.application.goods_type.first().id), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"],
            {"id": [f"A '{licence.application.case_type.reference}' Licence cannot be updated."]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists())
