from unittest import mock
from django.urls import reverse
from rest_framework import status

from api.applications.models import GoodOnApplication, GoodOnApplicationInternalDocument
from test_helpers.clients import DataTestClient

from api.applications.tests.factories import StandardApplicationFactory
from api.goods.tests.factories import GoodFactory
from api.organisations.tests.factories import OrganisationFactory


class DocumentGoodOnApplicationInternalTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)
        self.good_on_application = GoodOnApplication.objects.get(application=self.application)
        self.good_on_application_internal_doc = self.create_good_on_application_internal_document(
            good_on_application=self.good_on_application,
            name="test name",
            s3_key="evidence_file.12_20_20_48791_jpg",
            document_title="test title",
        )

    @mock.patch("api.documents.libraries.s3_operations.delete_file")
    @mock.patch("api.documents.libraries.s3_operations.get_object")
    def test_document_good_on_application_internal_document_saved(self, mock_delete_file, mock_get_file):

        good_on_application_id = str(self.good_on_application.id)
        url = reverse(
            "goods:documents_good_on_application_internal", kwargs={"goods_on_application_pk": good_on_application_id}
        )
        data = {
            "name": "test saved",
            "s3_key": "saved_jpg",
            "size": 2000,
            "document_title": "test saved title",
        }

        response = self.client.post(url, data, **self.exporter_headers)
        new_internal_doc = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data["good_on_application"] = str(GoodOnApplicationInternalDocument.objects.last().good_on_application_id)
        self.assertEqual(new_internal_doc, {"document": data})

    def test_document_good_on_application_internal_document_error(self):
        good_id = str(self.good_on_application.id)
        url = reverse("goods:documents_good_on_application_internal", kwargs={"goods_on_application_pk": str(good_id)})
        data = {}
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch("api.documents.libraries.s3_operations.delete_file")
    def test_document_good_on_application_internal_document_delete(self, mock_delete_file):

        internal_doc_id = str(self.good_on_application_internal_doc.id)
        url = reverse("goods:document_internal_good_on_application_detail", kwargs={"doc_pk": internal_doc_id})
        response = self.client.delete(url, **self.exporter_headers)

        total_internal_docs = GoodOnApplicationInternalDocument.objects.filter(id=internal_doc_id).count()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total_internal_docs, 0)
        mock_delete_file.assert_called_once()

    def test_document_good_on_application_internal_document_edit(self):
        internal_doc_id = str(self.good_on_application_internal_doc.id)
        url = reverse("goods:document_internal_good_on_application_detail", kwargs={"doc_pk": internal_doc_id})
        data = {"document_title": "new title"}
        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        document_title = GoodOnApplicationInternalDocument.objects.get(id=internal_doc_id).document_title
        self.assertEqual(document_title, data["document_title"])

    def test_document_good_on_application_internal_document_get(self):
        internal_doc_id = str(self.good_on_application_internal_doc.id)
        url = reverse("goods:document_internal_good_on_application_detail", kwargs={"doc_pk": internal_doc_id})
        response = self.client.get(url, **self.exporter_headers)
        good_internal_doc_returned = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good_internal_doc_returned["document"]["id"], internal_doc_id)
