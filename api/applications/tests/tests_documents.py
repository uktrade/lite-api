import uuid
from unittest import mock

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.applications.libraries.case_status_helpers import get_case_statuses
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class DraftDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.draft = self.create_draft_standard_application(self.organisation, "Draft")
        self.url_draft = reverse("applications:application_documents", kwargs={"pk": self.draft.id})
        self.test_filename = "dog.jpg"

        self.editable_case_statuses = get_case_statuses(read_only=False)
        self.read_only_case_statuses = get_case_statuses(read_only=True)

        self.data = {
            "name": self.test_filename,
            "s3_key": self.test_filename,
            "size": 476,
            "description": "banana cake 1",
        }

        self.data2 = {
            "name": self.test_filename + "2",
            "s3_key": self.test_filename,
            "size": 476,
            "description": "banana cake 2",
        }

    @mock.patch("documents.tasks.scan_document_for_viruses.now")
    def test_upload_document_on_unsubmitted_application(self, mock_prepare_doc):
        """ Test success in adding a document to an unsubmitted application. """
        self.client.post(self.url_draft, data=self.data, **self.exporter_headers)

        response = self.client.get(self.url_draft, **self.exporter_headers)
        response_data = [
            {
                "name": document["name"],
                "s3_key": document["s3_key"],
                "size": document["size"],
                "description": document["description"],
            }
            for document in response.json()["documents"]
        ]

        self.assertEqual(len(response_data), 2)
        self.assertTrue(self.data in response_data)

    @mock.patch("documents.tasks.scan_document_for_viruses.now")
    def test_upload_multiple_documents_on_unsubmitted_application(self, mock_prepare_doc):
        """ Test success in adding multiple documents to an unsubmitted application. """
        data = [self.data, self.data2]
        self.client.post(self.url_draft, data=self.data, **self.exporter_headers)
        self.client.post(self.url_draft, data=self.data2, **self.exporter_headers)

        response = self.client.get(self.url_draft, **self.exporter_headers)
        response_data = [
            {
                "name": document["name"],
                "s3_key": document["s3_key"],
                "size": document["size"],
                "description": document["description"],
            }
            for document in response.json()["documents"]
        ]

        self.assertEqual(len(response_data), 3)
        for document in data:
            self.assertTrue(document in response_data)

    @mock.patch("documents.tasks.scan_document_for_viruses.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_individual_draft_document(self, mock_delete_s3, mock_prepare_doc):
        """ Test success in deleting a document from an unsubmitted application. """
        self.client.post(self.url_draft, data=self.data, **self.exporter_headers)
        response = self.client.get(self.url_draft, **self.exporter_headers)

        url = reverse(
            "applications:application_document",
            kwargs={"pk": self.draft.id, "doc_pk": response.json()["documents"][0]["id"],},
        )

        self.client.delete(url, **self.exporter_headers)
        mock_delete_s3.assert_called_once()

        response = self.client.get(self.url_draft, **self.exporter_headers)
        self.assertEqual(len(response.json()["documents"]), 1)

    def test_get_individual_draft_document(self):
        """ Test success in downloading a document from an unsubmitted application. """
        application_document = self.draft.applicationdocument_set.first()
        url = reverse(
            "applications:application_document", kwargs={"pk": self.draft.id, "doc_pk": application_document.id},
        )

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.json()["document"]["name"], application_document.name)
        self.assertEqual(response.json()["document"]["s3_key"], application_document.s3_key)
        self.assertEqual(response.json()["document"]["size"], application_document.size)

    @parameterized.expand(get_case_statuses(read_only=False))
    @mock.patch("documents.tasks.scan_document_for_viruses.now")
    def test_add_document_when_application_in_editable_state_success(self, editable_status, mock_prepare_doc):
        application = self.create_draft_standard_application(self.organisation)
        application.status = get_case_status_by_status(editable_status)
        application.save()

        url = reverse("applications:application_documents", kwargs={"pk": application.id})
        response = self.client.post(url, data=self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(application.applicationdocument_set.count(), 2)

    @parameterized.expand(get_case_statuses(read_only=False))
    @mock.patch("documents.tasks.scan_document_for_viruses.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_document_when_application_in_editable_state_success(
        self, editable_status, mock_delete_s3, mock_prepare_doc
    ):
        application = self.create_draft_standard_application(self.organisation)
        application.status = get_case_status_by_status(editable_status)
        application.save()

        url = reverse(
            "applications:application_document",
            kwargs={"pk": application.id, "doc_pk": application.applicationdocument_set.first().id,},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(application.applicationdocument_set.count(), 0)

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_add_document_when_application_in_read_only_state_failure(self, read_only_status):
        application = self.create_draft_standard_application(self.organisation)
        application.status = get_case_status_by_status(read_only_status)
        application.save()

        url = reverse("applications:application_documents", kwargs={"pk": application.id})
        response = self.client.post(url, data=self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(application.applicationdocument_set.count(), 1)

    @parameterized.expand(get_case_statuses(read_only=True))
    @mock.patch("documents.tasks.scan_document_for_viruses.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_document_when_application_in_read_only_state_failure(
        self, read_only_status, mock_delete_s3, mock_prepare_doc
    ):
        application = self.create_draft_standard_application(self.organisation)
        application.status = get_case_status_by_status(read_only_status)
        application.save()

        url = reverse("applications:application_document", kwargs={"pk": application.id, "doc_pk": uuid.uuid4()},)
        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(application.applicationdocument_set.count(), 1)
