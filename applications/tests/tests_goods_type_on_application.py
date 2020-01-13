from unittest import mock

from rest_framework import status
from rest_framework.reverse import reverse

from goodstype.document.models import GoodsTypeDocument
from goodstype.models import GoodsType
from test_helpers.clients import DataTestClient


class GoodsTypeOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.open_application = self.create_open_application(self.organisation)
        self.url = reverse("applications:application_goodstypes", kwargs={"pk": self.open_application.id},)
        self.data = {
            "description": "Widget",
            "is_good_controlled": True,
            "control_code": "ML1a",
            "is_good_incorporated": True,
        }

        self.hmrc_query = self.create_hmrc_query(self.organisation)
        self.document_url = reverse(
            "applications:goods_type_document",
            kwargs={"pk": self.hmrc_query.id, "goods_type_pk": GoodsType.objects.get(application=self.hmrc_query).id,},
        )
        self.new_document_data = {
            "name": "document_name.pdf",
            "s3_key": "s3_keykey.pdf",
            "size": 123456,
        }

    def test_get_goodstypes_on_open_application_as_exporter_user_success(self):
        response = self.client.get(self.url, self.data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(
            len(response.json()["goods"]), GoodsType.objects.filter(application=self.open_application).count(),
        )

    def test_create_goodstype_on_open_application_as_exporter_user_success(self):
        response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()["good"]
        self.assertEquals(response_data["description"], "Widget")
        self.assertEquals(response_data["is_good_controlled"], True)
        self.assertEquals(response_data["control_code"], "ML1a")
        self.assertEquals(response_data["is_good_incorporated"], True)

    def test_create_goodstype_on_hmrc_query_as_exporter_user_success(self):
        url = reverse("applications:application_goodstypes", kwargs={"pk": self.hmrc_query.id})

        data = {
            "description": "Widget",
            "is_good_controlled": True,
            "control_code": "ML1a",
        }

        response = self.client.post(url, data, **self.hmrc_exporter_headers)
        response_data = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(response_data["description"], "Widget")
        self.assertEquals(response_data["is_good_controlled"], True)
        self.assertEquals(response_data["control_code"], "ML1a")
        self.assertNotIn("is_good_incorporated", response_data)

    def test_create_goodstype_on_open_application_as_exporter_user_failure(self):
        data = {}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_goodstype_on_open_application_as_gov_user_failure(self):
        response = self.client.post(self.url, self.data, **self.gov_headers)

        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_goodstype_on_standard_application_as_exporter_user_failure(self):
        application = self.create_standard_application(self.organisation)
        url = reverse("applications:application_goodstypes", kwargs={"pk": application.id})

        data = {
            "description": "Widget",
            "is_good_controlled": True,
            "control_code": "ML1a",
            "is_good_incorporated": True,
        }

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_goodstype_from_open_application_as_exporter_user_success(self):
        self.create_open_application(self.organisation)
        all_goods_types = GoodsType.objects.all()
        goods_type_id = all_goods_types.first().id
        initial_goods_types_count = all_goods_types.count()
        url = reverse(
            "applications:application_goodstype",
            kwargs={"pk": self.open_application.id, "goodstype_pk": goods_type_id},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(GoodsType.objects.all().count(), initial_goods_types_count - 1)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_post_goods_type_document_success(self, prepare_document_function):
        """
        Given a draft HMRC query has been created
        And the draft contains a goods type
        And the goods type does not have a document attached
        When a document is submitted
        Then a 201 CREATED is returned
        """
        GoodsTypeDocument.objects.get(goods_type__application=self.hmrc_query).delete()
        count = GoodsTypeDocument.objects.count()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(count + 1, GoodsTypeDocument.objects.count())

    @mock.patch("documents.tasks.prepare_document.now")
    def test_get_goods_type_document_success(self, prepare_document_function):
        """
        Given a draft HMRC query has been created
        And the draft contains a goods type
        And the goods type has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached goods party document
        """
        response = self.client.get(self.document_url, **self.hmrc_exporter_headers)
        response_data = response.json()["document"]

        self.assertEqual(response_data["name"], self.new_document_data["name"])
        self.assertEqual(response_data["s3_key"], self.new_document_data["s3_key"])
        self.assertEqual(response_data["size"], self.new_document_data["size"])

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_goods_type_document_success(self, delete_s3_function, prepare_document_function):
        """
        Given a draft HMRC query has been created
        And the draft contains a goods type
        And the goods type has a document attached
        When there is an attempt to delete the document
        Then 204 NO CONTENT is returned
        """
        response = self.client.delete(self.document_url, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        delete_s3_function.assert_called_once()

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_goods_type_success(self, delete_s3_function, prepare_document_function):
        """
        Given a draft HMRC query has been created
        And the draft contains a goods type
        And the goods type has a document attached
        When there is an attempt to delete goods type
        Then 200 OK is returned
        """
        url = reverse(
            "applications:application_goodstype",
            kwargs={"pk": self.hmrc_query.id, "goodstype_pk": GoodsType.objects.get(application=self.hmrc_query).id,},
        )
        goods_type_count = GoodsType.objects.count()
        goods_type_doc_count = GoodsTypeDocument.objects.count()

        response = self.client.delete(url, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(goods_type_count - 1, GoodsType.objects.count())
        self.assertEqual(goods_type_doc_count - 1, GoodsTypeDocument.objects.count())
        delete_s3_function.assert_called_once()
