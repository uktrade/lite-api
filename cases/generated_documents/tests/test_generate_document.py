from unittest import mock

from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseTypeEnum
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseActivity
from users.models import ExporterNotification
from letter_templates.models import LetterTemplate
from lite_content.lite_api.cases import GeneratedDocumentsEndpoint
from picklists.enums import PickListStatus, PicklistType
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class GenerateDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item(
            "#1", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
        )
        self.letter_layout = LetterLayout.objects.first()
        self.letter_template = LetterTemplate.objects.create(name="SIEL", layout=self.letter_layout,)
        self.letter_template.case_types.add(CaseTypeEnum.APPLICATION)
        self.letter_template.letter_paragraphs.add(self.picklist_item)
        self.case = self.create_standard_application_case(self.organisation)
        self.data = {"template": str(self.letter_template.id), "text": "sample"}
        self.content_type = ContentType.objects.get_for_model(GeneratedCaseDocument)

    @mock.patch("cases.generated_documents.views.html_to_pdf")
    @mock.patch("cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_success(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None

        url = reverse("cases:generated_documents:generated_documents", kwargs={"pk": str(self.case.pk)})
        response = self.client.post(url, **self.gov_headers, data=self.data)

        upload_bytes_file_func.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(GeneratedCaseDocument.objects.count() == 1)
        self.assertTrue(
            ExporterNotification.objects.filter(
                user=self.exporter_user, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count()
            == 1
        )

    @mock.patch("cases.generated_documents.views.html_to_pdf")
    @mock.patch("cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_when_html_to_pdf_throws_error_failure(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.side_effect = Exception("Failed to convert html to pdf")

        url = reverse("cases:generated_documents:generated_documents", kwargs={"pk": str(self.case.pk)})
        response = self.client.post(url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()["errors"], [GeneratedDocumentsEndpoint.PDF_ERROR])
        self.assertTrue(GeneratedCaseDocument.objects.count() == 0)
        self.assertTrue(CaseActivity.objects.count() == 0)
        self.assertTrue(
            ExporterNotification.objects.filter(
                user=self.exporter_user, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count()
            == 0
        )
        upload_bytes_file_func.assert_not_called()

    @mock.patch("cases.generated_documents.views.html_to_pdf")
    @mock.patch("cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_when_s3_throws_error_failure(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.side_effect = Exception("Failed to upload document")

        url = reverse("cases:generated_documents:generated_documents", kwargs={"pk": str(self.case.pk)})
        response = self.client.post(url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()["errors"], [GeneratedDocumentsEndpoint.UPLOAD_ERROR])
        self.assertTrue(GeneratedCaseDocument.objects.count() == 0)
        self.assertTrue(CaseActivity.objects.count() == 0)
        self.assertTrue(
            ExporterNotification.objects.filter(
                user=self.exporter_user, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count()
            == 0
        )

    def test_get_document_preview_success(self):
        url = (
            reverse("cases:generated_documents:preview", kwargs={"pk": str(self.case.pk)})
            + "?template="
            + str(self.letter_template.id)
            + "&text=Sample"
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("preview" in response.json())
        preview = response.json()["preview"]
        for html_tag in ["<style>", "</style>"]:
            self.assertTrue(html_tag in preview)

    def test_get_document_preview_without_template_query_param_failure(self):
        url = reverse("cases:generated_documents:preview", kwargs={"pk": str(self.case.pk)})
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertTrue("errors" in body)
        self.assertEqual(body["errors"], [GeneratedDocumentsEndpoint.MISSING_TEMPLATE])

    def test_get_document_preview_without_text_query_param_failure(self):
        url = (
            reverse("cases:generated_documents:preview", kwargs={"pk": str(self.case.pk)})
            + "?template="
            + str(self.letter_template.id)
        )

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertTrue("errors" in body)
        self.assertEqual(body["errors"], [GeneratedDocumentsEndpoint.MISSING_TEXT])

    @mock.patch("cases.generated_documents.helpers.generate_preview")
    @mock.patch("cases.generated_documents.views.html_to_pdf")
    @mock.patch("cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_get_document_preview_when_get_html_contains_errors_failure(
        self, upload_bytes_file_func, html_to_pdf_func, generate_preview_func
    ):
        generate_preview_func.return_value = dict(error="Failed to get preview")

        url = (
            reverse("cases:generated_documents:preview", kwargs={"pk": str(self.case.pk)})
            + "?template="
            + str(self.letter_template.id)
            + "&text=Sample"
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertTrue("errors" in body)
        self.assertEqual(body["errors"], ["Failed to get preview"])
        html_to_pdf_func.assert_not_called()
        upload_bytes_file_func.assert_not_called()
