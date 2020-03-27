from lite_content.lite_api import strings
from django.urls import reverse
from rest_framework import status

from applications.models import SiteOnApplication, CountryOnApplication
from cases.models import Case
from goodstype.models import GoodsType
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class OpenApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_open_application(self.organisation)
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

    def test_standard_application_declaration_submit_success(self):
        data = {
            "submit_declaration": True,
            "agreed_to_declaration": True,
            "agreed_to_foi": True,
        }

        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        case = Case.objects.get()
        self.assertEqual(case.id, self.draft.id)
        self.assertIsNotNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.SUBMITTED)
        self.assertEqual(case.baseapplication.agreed_to_foi, True)

    def test_standard_application_declaration_submit_tcs_false_failure(self):
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
