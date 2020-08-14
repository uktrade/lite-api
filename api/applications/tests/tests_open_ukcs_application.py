from django.test import tag
from django.urls import reverse
from rest_framework import status

from api.applications.enums import ApplicationExportType, GoodsTypeCategory
from api.applications.models import OpenApplication, CountryOnApplication
from cases.enums import CaseTypeReferenceEnum
from api.goodstype.models import GoodsType
from static.countries.helpers import get_country
from static.countries.models import Country
from test_helpers.clients import DataTestClient


class OpenUKCSTests(DataTestClient):
    url = reverse("applications:applications")

    def test_create_draft_open_ukcs_application_generates_goods(self):
        data = {
            "name": "Test",
            "application_type": CaseTypeReferenceEnum.OIEL,
            "export_type": ApplicationExportType.PERMANENT,
            "goodstype_category": GoodsTypeCategory.UK_CONTINENTAL_SHELF,
            "contains_firearm_goods": True,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OpenApplication.objects.count(), 1)

    def test_only_ukcs_added_ukcs(self):
        data = {
            "name": "Test",
            "export_type": ApplicationExportType.PERMANENT,
            "application_type": CaseTypeReferenceEnum.OIEL,
            "goodstype_category": GoodsTypeCategory.UK_CONTINENTAL_SHELF,
            "contains_firearm_goods": True,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CountryOnApplication.objects.filter(application=OpenApplication.objects.first()).count(), 1,
        )
        self.assertEqual(
            CountryOnApplication.objects.get(application=OpenApplication.objects.first()).country,
            Country.objects.get(id="UKCS"),
        )

    def test_cannot_change_countries_on_ukcs_application(self):
        application = self.create_draft_open_application(organisation=self.organisation)
        application.goodstype_category = GoodsTypeCategory.UK_CONTINENTAL_SHELF
        application.save()
        initial_countries_count = CountryOnApplication.objects.filter(application=application).count()
        data = {"countries": Country.objects.all()[:10].values_list("id", flat=True)}
        url = reverse("applications:countries", kwargs={"pk": application.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CountryOnApplication.objects.filter(application=application).count(), initial_countries_count)

    def test_cannot_change_countries_on_goodstype_on_ukcs_application(self):
        country_1 = get_country("ES")
        country_2 = get_country("US")
        country_3 = get_country("FR")

        application = self.create_draft_open_application(organisation=self.organisation)
        application.goodstype_category = GoodsTypeCategory.UK_CONTINENTAL_SHELF
        application.save()
        goodstype = GoodsType.objects.filter(application=application).first()
        initial_countries_count = goodstype.countries.count()
        data = {str(goodstype.id): [country_1.id, country_2.id, country_3.id]}
        url = reverse("applications:application_goodstype_assign_countries", kwargs={"pk": application.id})
        response = self.client.put(url, data, **self.exporter_headers)

        goodstype.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(goodstype.countries.count(), initial_countries_count)
