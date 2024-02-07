from rest_framework import status
from rest_framework.reverse import reverse

from api.goodstype.models import GoodsType
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from test_helpers.clients import DataTestClient


class GoodsTypeOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.open_application = self.create_draft_open_application(self.organisation)
        self.url = reverse(
            "applications:application_goodstypes",
            kwargs={"pk": self.open_application.id},
        )
        self.data = {
            "description": "Widget",
            "is_good_controlled": True,
            "control_list_entries": ["ML1a"],
            "is_good_incorporated": True,
        }
        self.new_document_data = {
            "name": "document_name.pdf",
            "s3_key": "s3_keykey.pdf",
            "size": 123456,
        }

    def test_create_goodstype_on_open_application_as_exporter_user_success(self):
        response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()["good"]
        self.assertEqual(response_data["description"], "Widget")
        self.assertEqual(response_data["is_good_controlled"], True)
        self.assertEqual(len(response_data["control_list_entries"]), 1)
        self.assertEqual(response_data["control_list_entries"][0]["rating"], "ML1a")
        self.assertEqual(response_data["control_list_entries"][0]["text"], get_control_list_entry("ML1a").text)
        self.assertEqual(response_data["is_good_incorporated"], True)

    def test_create_goodstype_multiple_clcs_on_open_application_as_exporter_user_success(self):
        self.data["control_list_entries"] = ["ML1a", "ML1b"]
        response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()["good"]
        self.assertEqual(response_data["description"], "Widget")
        self.assertEqual(response_data["is_good_controlled"], True)
        self.assertEqual(len(response_data["control_list_entries"]), len(self.data["control_list_entries"]))
        for item in response_data["control_list_entries"]:
            actual_rating = item["rating"]
            self.assertTrue(actual_rating in self.data["control_list_entries"])
            self.assertEqual(item["text"], get_control_list_entry(actual_rating).text)
        self.assertEqual(response_data["is_good_incorporated"], True)

    def test_create_goodstype_on_open_application_as_exporter_user_failure(self):
        data = {}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_goodstype_on_open_application_as_gov_user_failure(self):
        response = self.client.post(self.url, self.data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_goodstype_on_standard_application_as_exporter_user_failure(self):
        # Goodstypes only valid on HMRC and Open applications.
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:application_goodstypes", kwargs={"pk": application.id})

        data = {
            "description": "Widget",
            "is_good_controlled": True,
            "control_list_entry": ["ML1a"],
            "is_good_incorporated": True,
        }

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_goodstype_from_open_application_as_exporter_user_success(self):
        self.create_draft_open_application(self.organisation)
        all_goods_types = GoodsType.objects.all()
        goods_type_id = all_goods_types.first().id
        initial_goods_types_count = all_goods_types.count()
        url = reverse(
            "applications:application_goodstype",
            kwargs={"pk": self.open_application.id, "goodstype_pk": goods_type_id},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GoodsType.objects.all().count(), initial_goods_types_count - 1)
