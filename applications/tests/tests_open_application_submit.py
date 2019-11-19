from django.urls import reverse
from rest_framework import status

from applications.models import SiteOnApplication, CountryOnApplication
from cases.models import Case
from content_strings.strings import get_string
from goodstype.models import GoodsType
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class OpenApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_open_application(self.organisation)
        self.url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
		self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_submit_open_application_success(self):
        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get()
        self.assertEqual(case.application.id, self.draft.id)
        self.assertIsNotNone(case.application.submitted_at)
        self.assertEqual(case.application.status.status, CaseStatusEnum.SUBMITTED)

    def test_submit_open_application_without_site_failure(self):
        SiteOnApplication.objects.get(application=self.draft).delete()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response, text=get_string("applications.generic.no_location_set"), status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_open_application_without_goods_type_failure(self):
        GoodsType.objects.filter(application=self.draft).delete()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response, text=get_string("applications.open.no_goods_set"), status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_open_application_without_destination_failure(self):
        CountryOnApplication.objects.get(application=self.draft).delete()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response, text=get_string("applications.open.no_countries_set"), status_code=status.HTTP_400_BAD_REQUEST,
        )
