from django.test import tag
from django.urls import reverse
from rest_framework import status

from applications.enums import ApplicationExportType, GoodsTypeCategory
from applications.models import OpenApplication, CountryOnApplication
from cases.enums import CaseTypeReferenceEnum
from goodstype.models import GoodsType
from goodstype.tests.factories import GoodsTypeFactory
from static.countries.models import Country
from test_helpers.clients import DataTestClient


class OpenMediaTests(DataTestClient):
    url = reverse("applications:applications")

    @tag("1230", "media")
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

    @tag("1230")
    def test_export_type_is_set_to_temporary(self):
        data = {
            "name": "Test",
            "application_type": CaseTypeReferenceEnum.OIEL,
            "goodstype_category": GoodsTypeCategory.MEDIA,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OpenApplication.objects.first().export_type, ApplicationExportType.TEMPORARY)

    @tag("1230")
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

    @tag("1230")
    def test_all_countries_added_media(self):
        data = {
            "name": "Test",
            "export_type": ApplicationExportType.PERMANENT,
            "application_type": CaseTypeReferenceEnum.OIEL,
            "goodstype_category": GoodsTypeCategory.MEDIA,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CountryOnApplication.objects.filter(application=OpenApplication.objects.first()).count(),
            Country.objects.count(),
        )

    @tag("1230", "no-add")
    def test_cannot_add_goodstypes_on_media_application(self):
        application = self.create_draft_open_application(organisation=self.organisation)
        application.goodstype_category = GoodsTypeCategory.MEDIA
        application.save()
        initial_goods_count = GoodsType.objects.all().count()
        url = reverse("applications:application_goodstypes", kwargs={"pk": application.id})

        response = self.client.post(url, "", **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GoodsType.objects.all().count(), initial_goods_count)

    @tag("1230")
    def test_remove_goodstype_from_open_application_as_exporter_user_success(self):
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
