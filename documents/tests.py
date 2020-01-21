from unittest import mock

from django.http import StreamingHttpResponse
from django.urls import reverse

from test_helpers.clients import DataTestClient


class CaseDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.file = self.create_case_document(self.case, self.gov_user, "Test")
        self.url = reverse("documents:case_download", kwargs={"case_pk": self.case.id, "file_pk": self.file.id})

    @mock.patch("documents.libraries.s3_operations.get_object")
    def test_download_success(self, get_object_function):
        response = self.client.get(self.url, **self.exporter_headers)

        get_object_function.assert_called_once()
        self.assertTrue(isinstance(response, StreamingHttpResponse))
        self.assertTrue(f'filename="{self.file.name}"' in response._headers["content-disposition"][1])
