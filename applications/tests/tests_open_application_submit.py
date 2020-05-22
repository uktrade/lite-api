from uuid import UUID

from django.urls import reverse
from rest_framework import status

from applications.enums import ApplicationExportType
from applications.models import SiteOnApplication, CountryOnApplication
from audit_trail.enums import AuditType
from audit_trail.models import Audit
from cases.enums import CaseTypeEnum
from cases.models import Case, CaseType
from flags.enums import SystemFlags
from goodstype.models import GoodsType
from lite_content.lite_api import strings
from static.statuses.enums import CaseStatusEnum
from static.trade_control.enums import TradeControlActivity, TradeControlProductCategory
from test_helpers.clients import DataTestClient


class OpenApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_open_application(self.organisation)
        coa = CountryOnApplication.objects.get(application=self.draft)
        coa.contract_types = "[navy]"
        coa.save()
        self.url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_submit_open_application_before_declaration_success(self):
        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get()
        self.assertEqual(case.id, self.draft.id)
        self.assertIsNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.DRAFT)

    def test_submit_open_application_without_site_or_external_location_failure(self):
        SiteOnApplication.objects.get(application=self.draft).delete()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Generic.NO_LOCATION_SET, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_open_application_without_goods_type_failure(self):
        GoodsType.objects.filter(application=self.draft).delete()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Open.NO_GOODS_SET, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_open_application_without_destination_failure(self):
        CountryOnApplication.objects.get(application=self.draft).delete()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Open.NO_COUNTRIES_SET, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_open_application_without_end_use_details_failure(self):
        self.draft.intended_end_use = ""
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Generic.NO_END_USE_DETAILS, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_open_application_declaration_submit_success(self):
        data = {
            "submit_declaration": True,
            "agreed_to_declaration": True,
            "agreed_to_foi": True,
        }
        case = Case.objects.get()
        self.assertEqual(case.status.status, CaseStatusEnum.DRAFT)

        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        case.refresh_from_db()
        self.assertEqual(case.id, self.draft.id)
        self.assertIsNotNone(case.submitted_at)
        self.assertNotEqual(case.status.status, CaseStatusEnum.DRAFT)
        self.assertEqual(case.baseapplication.agreed_to_foi, True)
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_CHECK_REQUIRED) in case.flags.values_list("id", flat=True))

        case_status_audits = Audit.objects.filter(target_object_id=case.id, verb=AuditType.UPDATED_STATUS).values_list(
            "payload", flat=True
        )
        self.assertIn(
            {
                "status": {
                    "new": CaseStatusEnum.get_text(CaseStatusEnum.SUBMITTED),
                    "old": CaseStatusEnum.get_text(CaseStatusEnum.DRAFT),
                }
            },
            case_status_audits,
        )

    def test_submit_open_application_declaration_submit_tcs_false_failure(self):
        data = {
            "submit_declaration": True,
            "agreed_to_declaration": False,
            "agreed_to_foi": True,
        }

        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["errors"]
        self.assertEqual(errors["agreed_to_declaration"], [strings.Applications.Generic.AGREEMENT_TO_TCS_REQUIRED])

    def test_submit_open_application_temporary_with_temp_export_details_success(self):
        self.draft.export_type = ApplicationExportType.TEMPORARY
        self.draft.temp_export_details = "reasons why this export is a temporary one"
        self.draft.is_temp_direct_control = False
        self.draft.proposed_return_date = "2020-05-11"
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_submit_open_application_temporary_without_temp_export_details_failure(self):
        self.draft.export_type = ApplicationExportType.TEMPORARY
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Generic.NO_TEMPORARY_EXPORT_DETAILS,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_open_application_temporary_with_partial_temp_export_details_failure(self):
        self.draft.export_type = ApplicationExportType.TEMPORARY
        self.draft.temp_export_details = "reasons why this export is a temporary one"
        self.draft.proposed_return_date = "2020-05-11"
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Generic.NO_TEMPORARY_EXPORT_DETAILS,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_open_trade_control_application_maritime_activity_adds_flag(self):
        self.draft.case_type = CaseType.objects.get(id=CaseTypeEnum.OICL.id)
        self.draft.trade_control_activity = TradeControlActivity.MARITIME_ANTI_PIRACY
        self.draft.trade_control_product_categories = [key for key, _ in TradeControlProductCategory.choices]
        self.draft.save()
        data = {"submit_declaration": True, "agreed_to_declaration": True, "agreed_to_foi": True}

        response = self.client.put(self.url, data=data, **self.exporter_headers)
        self.draft.refresh_from_db()
        case_flags = [str(flag_id) for flag_id in self.draft.flags.values_list("id", flat=True)]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(SystemFlags.MARITIME_ANTI_PIRACY_ID, case_flags)


