import uuid
from unittest import mock

from django.urls import reverse
from parameterized import parameterized
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_207_MULTI_STATUS, HTTP_208_ALREADY_REPORTED
from django.test import override_settings

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceType, AdviceLevel, CaseTypeEnum
from api.cases.models import CaseType
from api.cases.tests.factories import GoodCountryDecisionFactory
from api.goodstype.models import GoodsType
from api.licences.enums import LicenceStatus, HMRCIntegrationActionEnum
from api.licences.models import HMRCIntegrationUsageData, Licence
from api.licences.tests.factories import GoodOnLicenceFactory
from api.open_general_licences.tests.factories import OpenGeneralLicenceFactory, OpenGeneralLicenceCaseFactory
from api.staticdata.countries.models import Country
from test_helpers.clients import DataTestClient


class HMRCIntegrationUsageTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:hmrc_integration")

    def create_siel_licence(self):
        standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        licence = self.create_licence(standard_application, status=LicenceStatus.ISSUED)
        self._create_good_on_licence(licence, standard_application.goods.first())
        return licence

    def create_f680_licence(self):
        f680_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.F680)
        self.create_advice(self.gov_user, f680_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        licence = self.create_licence(f680_application, status=LicenceStatus.ISSUED)
        self._create_good_on_licence(licence, f680_application.goods.first())
        return licence

    def create_gifting_licence(self):
        gifting_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.GIFTING)
        self.create_advice(self.gov_user, gifting_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        licence = self.create_licence(gifting_application, status=LicenceStatus.ISSUED)
        self._create_good_on_licence(licence, gifting_application.goods.first())
        return licence

    def create_exhibition_licence(self):
        exhibition_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.EXHIBITION)
        self.create_advice(self.gov_user, exhibition_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        licence = self.create_licence(exhibition_application, status=LicenceStatus.ISSUED)
        self._create_good_on_licence(licence, exhibition_application.goods.first())
        return licence

    def create_ogl_licence(self):
        open_general_licence = OpenGeneralLicenceFactory(case_type=CaseType.objects.get(id=CaseTypeEnum.OGEL.id))
        open_general_licence_case = OpenGeneralLicenceCaseFactory(
            open_general_licence=open_general_licence,
            site=self.organisation.primary_site,
            organisation=self.organisation,
        )
        licence = Licence.objects.get(case=open_general_licence_case)
        return licence

    def create_open_licence(self):
        open_application = self.create_open_application_case(self.organisation, CaseTypeEnum.EXHIBITION)
        goods = GoodsType.objects.filter(application=open_application)
        country = Country.objects.first()
        for good in goods:
            GoodCountryDecisionFactory(
                case=open_application,
                country=country,
                goods_type=good,
                approve=True,
            )
        licence = self.create_licence(open_application, status=LicenceStatus.ISSUED)
        return licence

    def _create_good_on_licence(self, licence, good_on_application):
        GoodOnLicenceFactory(
            good=good_on_application,
            licence=licence,
            quantity=good_on_application.quantity,
            usage=0.0,
            value=good_on_application.value,
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_accepted_licence_standard_applications(self, create_licence):
        licence = create_licence(self)
        gol_first = licence.goods.first()
        original_usage = gol_first.usage
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(gol_first.good.id), "usage": usage_data}],
        }

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        gol_first.refresh_from_db()
        self.assertEqual(
            response.json()["licences"]["accepted"],
            [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(gol_first.usage, original_usage + usage_data)
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence).exists())
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_PRODUCT_USAGE,
                payload={
                    "product_name": gol_first.good.good.name or gol_first.good.good.description,
                    "licence_reference": licence.reference_code,
                    "usage": original_usage + usage_data,
                    "quantity": gol_first.quantity,
                },
            ).exists()
        )

    def test_update_usages_accepted_licence_open_application(self):
        licence = self.create_open_licence()
        good = GoodsType.objects.filter(application=licence.case).first()
        original_usage = good.usage
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(good.id), "usage": usage_data}],
        }

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": [licence_update]})
        good.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"],
            [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(good.usage, original_usage + usage_data)
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence).exists())
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_PRODUCT_USAGE,
                payload={
                    "product_name": good.description,
                    "licence_reference": licence.reference_code,
                    "usage": original_usage + usage_data,
                    "quantity": 0,
                },
            ).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_all_goods_exhausted_on_licence(self, create_licence):
        licence = create_licence(self)
        gol = licence.goods.first()
        original_usage = gol.usage
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        gol.quantity = original_usage + usage_data
        gol.save()
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(gol.good.id), "usage": usage_data}],
        }

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"],
            [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(licence.goods.first().usage, original_usage + usage_data)
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.ISSUED)

    @override_settings(LITE_HMRC_INTEGRATION_ENABLED=True)
    @mock.patch("api.licences.celery_tasks.schedule_licence_details_to_lite_hmrc")
    def test_update_usages_all_goods_exhausted_when_action_is_open_does_inform_hmrc_of_licence(
        self, schedule_licence_details_to_lite_hmrc
    ):
        schedule_licence_details_to_lite_hmrc.return_value = None
        licence = self.create_siel_licence()
        gol = licence.goods.first()
        original_usage = gol.usage
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        gol.quantity = original_usage + usage_data
        gol.save()
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(gol.good.id), "usage": usage_data}],
        }

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"],
            [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(licence.goods.first().usage, original_usage + usage_data)
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.ISSUED)

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_usage_data_id_already_reported(self, create_licence):
        licence = create_licence(self)
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(licence.goods.first().good.id), "usage": usage_data}],
        }
        self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": [licence_update]})
        original_usage = licence.goods.first().usage

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_208_ALREADY_REPORTED)
        self.assertEqual(licence.goods.first().usage, original_usage)
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_usage_data_id_bad_request(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_data = 10

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(licence.id),
                        "action": HMRCIntegrationActionEnum.OPEN,
                        "goods": [{"id": str(licence.goods.first().good.id), "usage": usage_data}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["usage_data_id"],
            ["This field is required."],
        )
        self.assertEqual(licence.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(licences=licence).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_licences_bad_request(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_data_id = str(uuid.uuid4())

        response = self.client.put(self.url, {"usage_data_id": usage_data_id})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"],
            ["This field is required."],
        )
        self.assertEqual(licence.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_licence_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        licence_update = {
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(licence.goods.first().good.id), "usage": usage_data}],
        }

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"],
            {"id": ["This field is required."]},
        )
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_licence_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_data_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_data_id": usage_data_id,
                "licences": [
                    {
                        "action": HMRCIntegrationActionEnum.OPEN,
                        "id": str(uuid.uuid4()),
                        "goods": [{"id": str(licence.goods.first().good.id), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"],
            {"id": ["Licence not found."]},
        )
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_action_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_data_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_data_id": usage_data_id,
                "licences": [
                    {
                        "id": str(licence.id),
                        "goods": [{"id": str(licence.goods.first().good.id), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"],
            {"action": ["This field is required."]},
        )
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_action_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_data_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_data_id": usage_data_id,
                "licences": [
                    {
                        "id": str(licence.id),
                        "action": "i_am_invalid",
                        "goods": [{"id": str(licence.goods.first().good.id), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"],
            {"action": [f"Must be one of {HMRCIntegrationActionEnum.from_hmrc}"]},
        )
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_goods_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_data_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_data_id": usage_data_id,
                "licences": [{"id": str(licence.id), "action": HMRCIntegrationActionEnum.OPEN}],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"],
            {"goods": ["This field is required."]},
        )
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_good_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_data_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_data_id": usage_data_id,
                "licences": [
                    {"id": str(licence.id), "action": HMRCIntegrationActionEnum.OPEN, "goods": [{"usage": 10}]}
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["rejected"][0]["errors"],
            {"id": ["This field is required."]},
        )
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_good_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_data_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_data_id": usage_data_id,
                "licences": [
                    {
                        "id": str(licence.id),
                        "action": HMRCIntegrationActionEnum.OPEN,
                        "goods": [{"id": str(uuid.uuid4()), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["rejected"][0]["errors"],
            {"id": ["Good not found on Licence."]},
        )
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_good_usage_rejected_licence(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_data_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_data_id": usage_data_id,
                "licences": [
                    {
                        "id": str(licence.id),
                        "action": HMRCIntegrationActionEnum.OPEN,
                        "goods": [{"id": str(licence.goods.first().good.id)}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["rejected"][0]["errors"],
            {"usage": ["This field is required."]},
        )
        self.assertEqual(licence.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_multiple_licences_invalid_licence_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        invalid_licence_id = str(uuid.uuid4())
        licence_updates = [
            {
                "id": str(licence.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(licence.goods.first().good.id), "usage": usage_data}],
            },
            {
                "id": invalid_licence_id,
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(licence.goods.first().good.id), "usage": usage_data}],
            },
        ]

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": licence_updates})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"],
            [licence_updates[0]],
        )
        self.assertEqual(response.json()["licences"]["rejected"][0]["errors"], {"id": ["Licence not found."]})
        self.assertEqual(licence.goods.first().usage, original_usage + usage_data)
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence).exists())
        self.assertFalse(
            HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=invalid_licence_id).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_multiple_licences_invalid_good_id_rejected_licence(self, create_licence):
        licence_1 = create_licence(self)
        licence_1_original_usage = licence_1.goods.first().usage
        licence_2 = create_licence(self)
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        licence_updates = [
            {
                "id": str(licence_1.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(licence_1.goods.first().good.id), "usage": usage_data}],
            },
            {
                "id": str(licence_2.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(uuid.uuid4()), "usage": usage_data}],
            },
        ]

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": licence_updates})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"],
            [licence_updates[0]],
        )
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["rejected"][0]["errors"],
            {"id": ["Good not found on Licence."]},
        )
        self.assertEqual(licence_1.goods.first().usage, licence_1_original_usage + usage_data)
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence_1).exists())
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence_2).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_multiple_goods_invalid_good_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        accepted_good = {"id": str(licence.goods.first().good.id), "usage": usage_data}
        rejected_good = {"id": str(uuid.uuid4()), "usage": usage_data}

        response = self.client.put(
            self.url,
            {
                "usage_data_id": usage_data_id,
                "licences": [
                    {
                        "id": str(licence.id),
                        "action": HMRCIntegrationActionEnum.OPEN,
                        "goods": [accepted_good, rejected_good],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["accepted"],
            [accepted_good],
        )
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["rejected"][0]["errors"],
            {"id": ["Good not found on Licence."]},
        )
        self.assertEqual(licence.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_multiple_licences_and_goods_invalid_good_id_rejected_licence(self, create_licence):
        usage_data_id = str(uuid.uuid4())
        usage_data = 10
        licence_1 = create_licence(self)
        licence_1_original_usage = licence_1.goods.first().usage
        licence_2 = create_licence(self)
        expected_accepted_good = {"id": str(licence_2.goods.first().good.id), "usage": usage_data}
        expected_rejected_good = {"id": str(uuid.uuid4()), "usage": usage_data}
        licence_updates = [
            {
                "id": str(licence_1.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(licence_1.goods.first().good.id), "usage": usage_data}],
            },
            {
                "id": str(licence_2.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [expected_accepted_good, expected_rejected_good],
            },
        ]

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": licence_updates})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [licence_updates[0]])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["accepted"],
            [expected_accepted_good],
        )
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["rejected"][0]["errors"],
            {"id": ["Good not found on Licence."]},
        )
        self.assertEqual(licence_1.goods.first().usage, licence_1_original_usage + usage_data)
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence_1).exists())
        self.assertFalse(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence_2).exists())

    def test_licence_usage_updated_with_same_product_added_multiple_times(self):
        standard_application = self.create_standard_application_case(self.organisation, num_products=5, reuse_good=True)
        self.create_advice(self.gov_user, standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        licence = self.create_licence(standard_application, status=LicenceStatus.ISSUED)
        self._create_good_on_licence(licence, standard_application.goods.first())

        quantity_used = 1
        original_usage = [gol.usage for gol in licence.goods.all()]
        usage_data_id = str(uuid.uuid4())
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(gol.good.id), "usage": 1} for gol in licence.goods.all()],
        }

        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"],
            [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(
            [gol.usage for gol in licence.goods.all()], [prev_usage + quantity_used for prev_usage in original_usage]
        )
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence).exists())
        for index, good_on_licence in enumerate(licence.goods.all()):
            self.assertTrue(
                Audit.objects.filter(
                    verb=AuditType.LICENCE_UPDATED_PRODUCT_USAGE,
                    payload={
                        "product_name": good_on_licence.good.good.name or good_on_licence.good.good.description,
                        "licence_reference": licence.reference_code,
                        "usage": original_usage[index] + quantity_used,
                        "quantity": good_on_licence.quantity,
                    },
                ).exists()
            )

    @parameterized.expand(
        [
            (5,),
            (8,),
        ]
    )
    def test_update_usages_standard_applications_partial_export(self, usage_data):
        licence = self.create_siel_licence()
        good_on_licence = licence.goods.first()
        usage_data_id = str(uuid.uuid4())
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(good_on_licence.good.id), "usage": usage_data}],
        }

        # update usage data for partial export
        response = self.client.put(self.url, {"usage_data_id": usage_data_id, "licences": [licence_update]})
        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        good_on_licence.refresh_from_db()
        self.assertEqual(response.json()["licences"]["accepted"], [licence_update])
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(good_on_licence.usage, usage_data)
        self.assertTrue(HMRCIntegrationUsageData.objects.filter(id=usage_data_id, licences=licence).exists())
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_PRODUCT_USAGE,
                payload={
                    "product_name": good_on_licence.good.good.name or good_on_licence.good.good.description,
                    "licence_reference": licence.reference_code,
                    "usage": usage_data,
                    "quantity": good_on_licence.quantity,
                },
            ).exists()
        )
