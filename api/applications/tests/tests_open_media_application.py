from django.test import tag
from django.urls import reverse
from rest_framework import status

from api.applications.enums import ApplicationExportType, GoodsTypeCategory
from api.applications.models import OpenApplication, CountryOnApplication
from api.cases.enums import CaseTypeReferenceEnum
from api.goodstype.models import GoodsType
from api.goodstype.tests.factories import GoodsTypeFactory
from api.static.countries.helpers import get_country
from api.static.countries.models import Country
from test_helpers.clients import DataTestClient


class OpenMediaTests(DataTestClient):
    url = reverse("applications:applications")

    def test_create_draft_open_media_application_generates_goods(self):
        data = {
            "name": "Test",
            "application_type": CaseTypeReferenceEnum.OIEL,
            "export_type": ApplicationExportType.TEMPORARY,
            "goodstype_category": GoodsTypeCategory.MEDIA,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OpenApplication.objects.count(), 1)
        self.assertEqual(GoodsType.objects.filter(application=OpenApplication.objects.first()).count(), 6)

    def test_export_type_is_set_to_temporary(self):
        data = {
            "name": "Test",
            "application_type": CaseTypeReferenceEnum.OIEL,
            "goodstype_category": GoodsTypeCategory.MEDIA,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OpenApplication.objects.first().export_type, ApplicationExportType.TEMPORARY)

    def test_export_type_override_permanent_to_temporary(self):
        data = {
            "name": "Test",
            "export_type": ApplicationExportType.PERMANENT,
            "application_type": CaseTypeReferenceEnum.OIEL,
            "goodstype_category": GoodsTypeCategory.MEDIA,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OpenApplication.objects.first().export_type, ApplicationExportType.TEMPORARY)

    def test_all_countries_added_media(self):
        data = {
            "name": "Test",
            "export_type": ApplicationExportType.PERMANENT,
            "application_type": CaseTypeReferenceEnum.OIEL,
            "goodstype_category": GoodsTypeCategory.MEDIA,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        returned_coa = CountryOnApplication.objects.filter(application=OpenApplication.objects.first())
        # Ensure the UK is not in the list of media destinations
        self.assertNotIn(get_country("GB"), returned_coa)
        self.assertEqual(returned_coa.count(), Country.exclude_special_countries.count() - 1)

    def test_cannot_add_goodstypes_on_media_application(self):
        application = self.create_draft_open_application(organisation=self.organisation)
        application.goodstype_category = GoodsTypeCategory.MEDIA
        application.save()
        initial_goods_count = GoodsType.objects.all().count()
        url = reverse("applications:application_goodstypes", kwargs={"pk": application.id})

        response = self.client.post(url, "", **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GoodsType.objects.all().count(), initial_goods_count)

    def test_cannot_remove_goodstype_from_open_media_application(self):
        self.create_draft_open_application(self.organisation)
        application = self.create_draft_open_application(organisation=self.organisation)
        application.goodstype_category = GoodsTypeCategory.MEDIA
        application.save()
        goodstype = GoodsTypeFactory(application=application)
        initial_goods_count = GoodsType.objects.all().count()
        url = reverse(
            "applications:application_goodstype", kwargs={"pk": application.id, "goodstype_pk": goodstype.id},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(GoodsType.objects.all().count(), initial_goods_count)

    def test_cannot_change_countries_on_media_application(self):
        application = self.create_draft_open_application(organisation=self.organisation)
        application.goodstype_category = GoodsTypeCategory.MEDIA
        application.save()
        initial_countries_count = CountryOnApplication.objects.filter(application=application).count()
        data = {"countries": Country.objects.all()[:10].values_list("id", flat=True)}
        url = reverse("applications:countries", kwargs={"pk": application.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CountryOnApplication.objects.filter(application=application).count(), initial_countries_count)

    def test_cannot_change_countries_on_goodstype_on_media_application(self):
        country_1 = get_country("ES")
        country_2 = get_country("US")
        country_3 = get_country("FR")

        application = self.create_draft_open_application(organisation=self.organisation)
        application.goodstype_category = GoodsTypeCategory.MEDIA
        application.save()
        goodstype = GoodsType.objects.filter(application=application).first()
        initial_countries_count = goodstype.countries.count()
        data = {str(goodstype.id): [country_1.id, country_2.id, country_3.id]}
        url = reverse("applications:application_goodstype_assign_countries", kwargs={"pk": application.id})
        response = self.client.put(url, data, **self.exporter_headers)

        goodstype.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(goodstype.countries.count(), initial_countries_count)
