from unittest import mock

from rest_framework import status
from rest_framework.reverse import reverse

from api.goodstype.document.models import GoodsTypeDocument
from api.goodstype.models import GoodsType
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from api.staticdata.control_list_entries.models import ControlListEntry
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

        self.hmrc_query = self.create_hmrc_query(self.organisation)
        self.document_url = reverse(
            "applications:goods_type_document",
            kwargs={
                "pk": self.hmrc_query.id,
                "goods_type_pk": GoodsType.objects.get(application=self.hmrc_query).id,
            },
        )
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

    @mock.patch("api.documents.libraries.s3_operations.get_object")
    @mock.patch("api.documents.libraries.av_operations.scan_file_for_viruses")
    def test_post_goods_type_document_success(self, mock_virus_scan, mock_s3_operations_get_object):
        """
        Given a draft HMRC query has been created
        And the draft contains a goods type
        And the goods type does not have a document attached
        When a document is submitted
        Then a 201 CREATED is returned
        """
        mock_s3_operations_get_object.return_value = self.new_document_data
        mock_virus_scan.return_value = False
        GoodsTypeDocument.objects.get(goods_type__application=self.hmrc_query).delete()
        count = GoodsTypeDocument.objects.count()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(count + 1, GoodsTypeDocument.objects.count())

    @mock.patch("api.documents.libraries.s3_operations.get_object")
    @mock.patch("api.documents.libraries.av_operations.scan_file_for_viruses")
    def test_get_goods_type_document_success(self, mock_virus_scan, mock_s3_operations_get_object):
        """
        Given a draft HMRC query has been created
        And the draft contains a goods type
        And the goods type has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached goods party document
        """
        mock_s3_operations_get_object.return_value = self.new_document_data
        mock_virus_scan.return_value = False
        response = self.client.get(self.document_url, **self.hmrc_exporter_headers)
        response_data = response.json()["document"]

        self.assertEqual(response_data["name"], self.new_document_data["name"])
        self.assertEqual(response_data["s3_key"], self.new_document_data["s3_key"])
        self.assertEqual(response_data["size"], self.new_document_data["size"])

    @mock.patch("api.documents.libraries.s3_operations.get_object")
    @mock.patch("api.documents.libraries.av_operations.scan_file_for_viruses")
    @mock.patch("api.documents.models.Document.delete_s3")
    def test_delete_goods_type_document_success(
        self, delete_s3_function, mock_virus_scan, mock_s3_operations_get_object
    ):
        """
        Given a draft HMRC query has been created
        And the draft contains a goods type
        And the goods type has a document attached
        When there is an attempt to delete the document
        Then 204 NO CONTENT is returned
        """
        mock_s3_operations_get_object.return_value = self.new_document_data
        mock_virus_scan.return_value = False
        response = self.client.delete(self.document_url, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        delete_s3_function.assert_called_once()

    @mock.patch("api.documents.libraries.s3_operations.get_object")
    @mock.patch("api.documents.libraries.av_operations.scan_file_for_viruses")
    @mock.patch("api.documents.models.Document.delete_s3")
    def test_delete_goods_type_success(self, delete_s3_function, mock_virus_scan, mock_s3_operations_get_object):
        """
        Given a draft HMRC query has been created
        And the draft contains a goods type
        And the goods type has a document attached
        When there is an attempt to delete goods type
        Then 200 OK is returned
        """
        mock_s3_operations_get_object.return_value = self.new_document_data
        mock_virus_scan.return_value = False
        url = reverse(
            "applications:application_goodstype",
            kwargs={
                "pk": self.hmrc_query.id,
                "goodstype_pk": GoodsType.objects.get(application=self.hmrc_query).id,
            },
        )
        goods_type_count = GoodsType.objects.count()
        goods_type_doc_count = GoodsTypeDocument.objects.count()

        response = self.client.delete(url, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(goods_type_count - 1, GoodsType.objects.count())
        self.assertEqual(goods_type_doc_count - 1, GoodsTypeDocument.objects.count())
        delete_s3_function.assert_called_once()
