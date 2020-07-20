import uuid
from unittest import mock

from django.urls import reverse
from parameterized import parameterized
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_207_MULTI_STATUS, HTTP_208_ALREADY_REPORTED

from audit_trail.enums import AuditType
from audit_trail.models import Audit
from cases.enums import AdviceType, AdviceLevel, CaseTypeEnum
from cases.models import CaseType
from goodstype.models import GoodsType
from licences.enums import LicenceStatus, HMRCIntegrationActionEnum
from licences.models import HMRCIntegrationUsageUpdate, Licence
from licences.tests.factories import GoodOnLicenceFactory
from open_general_licences.tests.factories import OpenGeneralLicenceFactory, OpenGeneralLicenceCaseFactory
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
        for good in goods:
            self.create_advice(
                self.gov_user, open_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL, goods_type=good
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
        original_usage = licence.goods.first().usage
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(licence.goods.first().good.good.id), "usage": usage_update}],
        }

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(licence.goods.first().usage, original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_GOOD_USAGE,
                payload={
                    "good_description": licence.goods.first().good.good.description,
                    "usage": original_usage + usage_update,
                    "licence": licence.reference_code,
                },
            ).exists()
        )

    def test_update_usages_accepted_licence_open_application(self):
        licence = self.create_open_licence()
        good = GoodsType.objects.filter(application=licence.case).first()
        original_usage = good.usage
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(good.id), "usage": usage_update}],
        }

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        good.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(good.usage, original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_GOOD_USAGE,
                payload={
                    "good_description": good.description,
                    "usage": original_usage + usage_update,
                    "licence": licence.reference_code,
                },
            ).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence], [create_ogl_licence]]
    )
    def test_update_usages_exhaust_licence_action(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())
        licence_update = {"id": str(licence.id), "action": HMRCIntegrationActionEnum.EXHAUST, "goods": []}

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.EXHAUSTED)
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_STATUS,
                payload={"licence": licence.reference_code, "status": LicenceStatus.EXHAUSTED},
            ).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence], [create_ogl_licence]]
    )
    def test_update_usages_cancel_licence_action(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())
        licence_update = {"id": str(licence.id), "action": HMRCIntegrationActionEnum.CANCEL, "goods": []}

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.CANCELLED)
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_STATUS,
                payload={"licence": licence.reference_code, "status": LicenceStatus.CANCELLED},
            ).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence], [create_ogl_licence]]
    )
    def test_update_usages_surrender_licence_action(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())
        licence_update = {"id": str(licence.id), "action": HMRCIntegrationActionEnum.SURRENDER, "goods": []}

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.SURRENDERED)
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_STATUS,
                payload={"licence": licence.reference_code, "status": LicenceStatus.SURRENDERED},
            ).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence], [create_ogl_licence]]
    )
    def test_update_usages_expire_licence_action(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())
        licence_update = {"id": str(licence.id), "action": HMRCIntegrationActionEnum.EXPIRE, "goods": []}

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.EXPIRED)
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_STATUS,
                payload={"licence": licence.reference_code, "status": LicenceStatus.EXPIRED},
            ).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_all_goods_exhausted_on_licence(self, create_licence):
        licence = create_licence(self)
        gol = licence.goods.first()
        original_usage = gol.usage
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        gol.quantity = original_usage + usage_update
        gol.save()
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(gol.good.good.id), "usage": usage_update}],
        }

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(licence.goods.first().usage, original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.EXHAUSTED)
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_STATUS,
                payload={"licence": licence.reference_code, "status": LicenceStatus.EXHAUSTED},
            ).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_when_action_is_exhaust_then_goods_still_get_updated_on_licence(self, create_licence):
        licence = create_licence(self)
        gol = licence.goods.first()
        original_usage = gol.usage
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        gol.quantity = original_usage + usage_update
        gol.save()
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.EXHAUST,
            "goods": [{"id": str(gol.good.good.id), "usage": usage_update}],
        }

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(licence.goods.first().usage, original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.EXHAUSTED)
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_STATUS,
                payload={"licence": licence.reference_code, "status": LicenceStatus.EXHAUSTED},
            ).exists()
        )

    @mock.patch("licences.models.LITE_HMRC_INTEGRATION_ENABLED", True)
    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_update_usages_all_goods_exhausted_when_action_is_exhaust_doesnt_create_task_to_inform_hmrc_of_licence(
        self, schedule_licence_for_hmrc_integration
    ):
        schedule_licence_for_hmrc_integration.return_value = None
        licence = self.create_siel_licence()
        gol = licence.goods.first()
        original_usage = gol.usage
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        gol.quantity = original_usage + usage_update
        gol.save()
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.EXHAUST,
            "goods": [{"id": str(gol.good.good.id), "usage": usage_update}],
        }

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(licence.goods.first().usage, original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.EXHAUSTED)
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_STATUS,
                payload={"licence": licence.reference_code, "status": LicenceStatus.EXHAUSTED},
            ).exists()
        )
        # If HMRC has sent an action to update the Licence status;
        # Assert that the licence being set to Exhausted via all good lines being exhausted does not trigger the
        # task to inform HMRC that the status has changed
        schedule_licence_for_hmrc_integration.assert_not_called()

    @mock.patch("licences.models.LITE_HMRC_INTEGRATION_ENABLED", True)
    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_update_usages_all_goods_exhausted_when_action_is_open_does_inform_hmrc_of_licence(
        self, schedule_licence_for_hmrc_integration
    ):
        schedule_licence_for_hmrc_integration.return_value = None
        licence = self.create_siel_licence()
        gol = licence.goods.first()
        original_usage = gol.usage
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        gol.quantity = original_usage + usage_update
        gol.save()
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(gol.good.good.id), "usage": usage_update}],
        }

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        licence.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_update],
        )
        self.assertEqual(response.json()["licences"]["rejected"], [])
        self.assertEqual(licence.goods.first().usage, original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertEqual(licence.status, LicenceStatus.EXHAUSTED)
        self.assertTrue(
            Audit.objects.filter(
                verb=AuditType.LICENCE_UPDATED_STATUS,
                payload={"licence": licence.reference_code, "status": LicenceStatus.EXHAUSTED},
            ).exists()
        )
        # Assert that the licence being set to Exhausted via all good lines being exhausted does trigger the
        # task to inform HMRC that the status has changed
        schedule_licence_for_hmrc_integration.assert_called_once()

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_usage_update_id_already_reported(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        licence_update = {
            "id": str(licence.id),
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(licence.goods.first().good.good.id), "usage": usage_update}],
        }
        self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})
        original_usage = licence.goods.first().usage

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_208_ALREADY_REPORTED)
        self.assertEqual(licence.goods.first().usage, original_usage)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_usage_update_id_bad_request(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_update = 10

        response = self.client.put(
            self.url,
            {
                "licences": [
                    {
                        "id": str(licence.id),
                        "action": HMRCIntegrationActionEnum.OPEN,
                        "goods": [{"id": str(licence.goods.first().good.good.id), "usage": usage_update}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["usage_update_id"], ["This field is required."],
        )
        self.assertEqual(licence.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(licences=licence).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_licences_bad_request(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_update_id = str(uuid.uuid4())

        response = self.client.put(self.url, {"usage_update_id": usage_update_id})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["licences"], ["This field is required."],
        )
        self.assertEqual(licence.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_licence_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        licence_update = {
            "action": HMRCIntegrationActionEnum.OPEN,
            "goods": [{"id": str(licence.goods.first().good.good.id), "usage": usage_update}],
        }

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": [licence_update]})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"id": ["This field is required."]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_licence_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_update_id": usage_update_id,
                "licences": [
                    {
                        "action": HMRCIntegrationActionEnum.OPEN,
                        "id": str(uuid.uuid4()),
                        "goods": [{"id": str(licence.goods.first().good.good.id), "usage": 10}],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"id": ["Licence not found."]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_action_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_update_id": usage_update_id,
                "licences": [
                    {"id": str(licence.id), "goods": [{"id": str(licence.goods.first().good.good.id), "usage": 10}],}
                ],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"action": ["This field is required."]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_action_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_update_id": usage_update_id,
                "licences": [
                    {
                        "id": str(licence.id),
                        "action": "i_am_invalid",
                        "goods": [{"id": str(licence.goods.first().good.good.id), "usage": 10}],
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
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_goods_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_update_id": usage_update_id,
                "licences": [{"id": str(licence.id), "action": HMRCIntegrationActionEnum.OPEN}],
            },
        )

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["errors"], {"goods": ["This field is required."]},
        )
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_good_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_update_id": usage_update_id,
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
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_invalid_good_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        usage_update_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_update_id": usage_update_id,
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
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_no_good_usage_rejected_licence(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_update_id = str(uuid.uuid4())

        response = self.client.put(
            self.url,
            {
                "usage_update_id": usage_update_id,
                "licences": [
                    {
                        "id": str(licence.id),
                        "action": HMRCIntegrationActionEnum.OPEN,
                        "goods": [{"id": str(licence.goods.first().good.good.id)}],
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
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_multiple_licences_invalid_licence_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        invalid_licence_id = str(uuid.uuid4())
        licence_updates = [
            {
                "id": str(licence.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(licence.goods.first().good.good.id), "usage": usage_update}],
            },
            {
                "id": invalid_licence_id,
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(licence.goods.first().good.good.id), "usage": usage_update}],
            },
        ]

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": licence_updates})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_updates[0]],
        )
        self.assertEqual(response.json()["licences"]["rejected"][0]["errors"], {"id": ["Licence not found."]})
        self.assertEqual(licence.goods.first().usage, original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence).exists())
        self.assertFalse(
            HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=invalid_licence_id).exists()
        )

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_multiple_licences_invalid_good_id_rejected_licence(self, create_licence):
        licence_1 = create_licence(self)
        licence_1_original_usage = licence_1.goods.first().usage
        licence_2 = create_licence(self)
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        licence_updates = [
            {
                "id": str(licence_1.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(licence_1.goods.first().good.good.id), "usage": usage_update}],
            },
            {
                "id": str(licence_2.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(uuid.uuid4()), "usage": usage_update}],
            },
        ]

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": licence_updates})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(
            response.json()["licences"]["accepted"], [licence_updates[0]],
        )
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["rejected"][0]["errors"],
            {"id": ["Good not found on Licence."]},
        )
        self.assertEqual(licence_1.goods.first().usage, licence_1_original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence_1).exists())
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence_2).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_multiple_goods_invalid_good_id_rejected_licence(self, create_licence):
        licence = create_licence(self)
        original_usage = licence.goods.first().usage
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        accepted_good = {"id": str(licence.goods.first().good.good.id), "usage": usage_update}
        rejected_good = {"id": str(uuid.uuid4()), "usage": usage_update}

        response = self.client.put(
            self.url,
            {
                "usage_update_id": usage_update_id,
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
            response.json()["licences"]["rejected"][0]["goods"]["accepted"], [accepted_good],
        )
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["rejected"][0]["errors"],
            {"id": ["Good not found on Licence."]},
        )
        self.assertEqual(licence.goods.first().usage, original_usage)
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id).exists())

    @parameterized.expand(
        [[create_siel_licence], [create_f680_licence], [create_gifting_licence], [create_exhibition_licence]]
    )
    def test_update_usages_multiple_licences_and_goods_invalid_good_id_rejected_licence(self, create_licence):
        usage_update_id = str(uuid.uuid4())
        usage_update = 10
        licence_1 = create_licence(self)
        licence_1_original_usage = licence_1.goods.first().usage
        licence_2 = create_licence(self)
        expected_accepted_good = {"id": str(licence_2.goods.first().good.good.id), "usage": usage_update}
        expected_rejected_good = {"id": str(uuid.uuid4()), "usage": usage_update}
        licence_updates = [
            {
                "id": str(licence_1.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [{"id": str(licence_1.goods.first().good.good.id), "usage": usage_update}],
            },
            {
                "id": str(licence_2.id),
                "action": HMRCIntegrationActionEnum.OPEN,
                "goods": [expected_accepted_good, expected_rejected_good],
            },
        ]

        response = self.client.put(self.url, {"usage_update_id": usage_update_id, "licences": licence_updates})

        self.assertEqual(response.status_code, HTTP_207_MULTI_STATUS)
        self.assertEqual(response.json()["licences"]["accepted"], [licence_updates[0]])
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["accepted"], [expected_accepted_good],
        )
        self.assertEqual(
            response.json()["licences"]["rejected"][0]["goods"]["rejected"][0]["errors"],
            {"id": ["Good not found on Licence."]},
        )
        self.assertEqual(licence_1.goods.first().usage, licence_1_original_usage + usage_update)
        self.assertTrue(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence_1).exists())
        self.assertFalse(HMRCIntegrationUsageUpdate.objects.filter(id=usage_update_id, licences=licence_2).exists())
