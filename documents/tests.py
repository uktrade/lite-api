import uuid
from unittest import mock

from django.http import StreamingHttpResponse
from django.urls import reverse
from rest_framework import status

from lite_content.lite_api.strings import Documents
from test_helpers.clients import DataTestClient


class CaseDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.file = self.create_case_document(self.case, self.gov_user, "Test")

    @mock.patch("documents.libraries.s3_operations.get_object")
    def test_download_case_document_success(self, get_object_function):
        url = reverse("documents:case_document", kwargs={"case_pk": self.case.id, "file_pk": self.file.id})

        response = self.client.get(url, **self.exporter_headers)

        get_object_function.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response, StreamingHttpResponse))
        self.assertTrue(f'filename="{self.file.name}"' in response._headers["content-disposition"][1])

    def test_download_case_document_invalid_organisation_failure(self):
        # Create an application with a document for a different organisation
        # Our test user shouldn't be able to access this
        other_org, user = self.create_organisation_with_exporter_user()
        other_application = self.create_standard_application(other_org)
        other_case = self.submit_application(other_application)
        other_file = self.create_case_document(other_case, self.gov_user, "Someone else's document")
        url = reverse("documents:case_document", kwargs={"case_pk": other_case.id, "file_pk": other_file.id})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(int(response.content.decode("utf-8")), status.HTTP_401_UNAUTHORIZED)

    def test_download_case_document_invalid_id_failure(self):
        url = reverse("documents:case_document", kwargs={"case_pk": self.case.id, "file_pk": uuid.uuid4()})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"errors": {"document": Documents.DOCUMENT_NOT_FOUND}})
