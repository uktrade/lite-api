import csv

from django.test import tag
from django.urls import reverse
from rest_framework import status

from applications.enums import ApplicationExportType, GoodsTypeCategory
from applications.models import OpenApplication
from cases.enums import CaseTypeReferenceEnum
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer
from static.control_list_entries.models import ControlListEntry
from test_helpers.clients import DataTestClient


class OpenMediaTests(DataTestClient):
    url = reverse("applications:applications")

    @tag("1230", "media")
    def test_create_draft_open_media_application_generates_goods(self):
        ControlListEntry.create("ML1b", "Info here", None, False)
        data = {
            "name": "Test",
            "application_type": CaseTypeReferenceEnum.OIEL,
            "export_type": ApplicationExportType.TEMPORARY,
            "goodstype_category": GoodsTypeCategory.MEDIA,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        print(response.json())
        print(GoodsType.objects.all())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OpenApplication.objects.count(), 1)
        self.assertEqual(GoodsType.objects.filter(application=OpenApplication.objects.first()), 6)

    @tag("csv")
    def test_get_the_fucking_rows_out_of_the_csv(self):

        ControlListEntry.create("ML1b", "Info here", None, False)

        with open("lite_content/lite_api/OEIL_products.csv", newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                if row["SUBTYPE"] == "MEDIA":
                    data = {
                        "application": self.create_draft_open_application(organisation=self.organisation),
                        "description": row["DESCRIPTION"],
                        "is_good_controlled": "True",
                        "is_good_incorporated": "False",
                        "control_list_entries": ["ML1a", "ML1b"],
                    }
                    serializer = GoodsTypeSerializer(data=data)
                    if serializer.is_valid():
                        serializer.save()

        # self.assertEqual(GoodsType.objects.count(), 6)

        for good in GoodsType.objects.all():
            print(good.description)
