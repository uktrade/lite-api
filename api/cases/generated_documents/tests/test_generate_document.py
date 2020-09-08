from unittest import mock

from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse

from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum, AdviceType
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.licences.enums import LicenceStatus
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient
from api.users.models import ExporterNotification


class GenerateDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.letter_template = self.create_letter_template(name="SIEL", case_types=[CaseTypeEnum.SIEL.id])
        self.case = self.create_standard_application_case(self.organisation)
        self.data = {"template": str(self.letter_template.id), "text": "sample", "visible_to_exporter": True}
        self.content_type = ContentType.objects.get_for_model(GeneratedCaseDocument)
        self.url = reverse("cases:generated_documents:generated_documents", kwargs={"pk": str(self.case.pk)})

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_success(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        html_to_pdf_func.assert_called_once()
        upload_bytes_file_func.assert_called_once()
        self.assertEqual(GeneratedCaseDocument.objects.count(), 1)
        self.assertEqual(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count(),
            1,
        )

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    @mock.patch("api.cases.generated_documents.views.sign_pdf")
    def test_generate_document_with_signature_success(self, upload_bytes_file_func, html_to_pdf_func, sign_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        sign_pdf_func.return_value = None
        template = self.create_letter_template(case_types=[CaseTypeEnum.SIEL.id], digital_signature=True)
        self.data["template"] = str(template.id)

        url = reverse("cases:generated_documents:generated_documents", kwargs={"pk": str(self.case.pk)})
        response = self.client.post(url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        html_to_pdf_func.assert_called_once()
        upload_bytes_file_func.assert_called_once()
        sign_pdf_func.assert_called_once()
        self.assertTrue(GeneratedCaseDocument.objects.count() == 1)
        self.assertTrue(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count()
            == 1
        )

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_with_hidden_template_success(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        template = self.create_letter_template(case_types=[CaseTypeEnum.SIEL.id], visible_to_exporter=False)
        self.data["template"] = str(template.id)

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        html_to_pdf_func.assert_called_once()
        upload_bytes_file_func.assert_called_once()
        self.assertEqual(GeneratedCaseDocument.objects.count(), 1)
        self.assertEqual(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count(),
            0,
        )
        self.assertEqual(GeneratedCaseDocument.objects.get().visible_to_exporter, False)

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_decision_document_success(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        self.data["visible_to_exporter"] = True
        self.data["advice_type"] = AdviceType.NO_LICENCE_REQUIRED

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        upload_bytes_file_func.assert_called_once()
        self.assertEqual(GeneratedCaseDocument.objects.filter(advice_type=AdviceType.NO_LICENCE_REQUIRED).count(), 1)
        # Ensure decision documents are hidden until complete
        self.assertEqual(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count(),
            0,
        )

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_licence_document_success(self, upload_bytes_file_func, html_to_pdf_func):
        licence = self.create_licence(self.case, status=LicenceStatus.DRAFT)
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        self.data["visible_to_exporter"] = True
        self.data["advice_type"] = AdviceType.APPROVE

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        html_to_pdf_func.assert_called_once()
        upload_bytes_file_func.assert_called_once()
        self.assertEqual(
            GeneratedCaseDocument.objects.filter(advice_type=AdviceType.APPROVE, licence=licence).count(), 1
        )
        # Ensure decision documents are hidden until complete
        self.assertEqual(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count(),
            0,
        )

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_licence_document_no_licence_failure(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        self.data["visible_to_exporter"] = True
        self.data["advice_type"] = AdviceType.APPROVE

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"], {"non_field_errors": [strings.Cases.GeneratedDocuments.LICENCE_ERROR]}
        )

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_new_licence_document_success(self, upload_bytes_file_func, html_to_pdf_func):
        licence = self.create_licence(self.case, status=LicenceStatus.DRAFT)
        self.create_generated_case_document(
            self.case, self.letter_template, advice_type=AdviceType.APPROVE, licence=licence, visible_to_exporter=False
        )
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        self.data["visible_to_exporter"] = True
        self.data["advice_type"] = AdviceType.APPROVE

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        upload_bytes_file_func.assert_called_once()
        # Ensure the old licence document is deleted
        self.assertEqual(GeneratedCaseDocument.objects.filter(advice_type=AdviceType.APPROVE).count(), 1)
        document = GeneratedCaseDocument.objects.get(advice_type=AdviceType.APPROVE)
        self.assertEqual(document.licence, licence)
        self.assertEqual(response.json()["generated_document"], str(document.id))
        # Ensure decision documents are hidden until complete
        self.assertEqual(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count(),
            0,
        )

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_when_html_to_pdf_throws_error_failure(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.side_effect = Exception("Failed to convert html to pdf")

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()["errors"], [strings.Cases.GeneratedDocuments.PDF_ERROR])
        self.assertEqual(GeneratedCaseDocument.objects.count(), 0)
        self.assertEqual(Audit.objects.count(), 1)
        self.assertEqual(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count(),
            0,
        )
        upload_bytes_file_func.assert_not_called()

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_when_s3_throws_error_failure(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.side_effect = Exception("Failed to upload document")

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()["errors"], [strings.Cases.GeneratedDocuments.UPLOAD_ERROR])
        self.assertEqual(GeneratedCaseDocument.objects.count(), 0)
        self.assertEqual(Audit.objects.count(), 1)
        self.assertEqual(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk, content_type=self.content_type, organisation=self.exporter_user.organisation
            ).count(),
            0,
        )

    def test_get_document_preview_success(self):
        text = "Sample"
        url = (
            reverse("cases:generated_documents:preview", kwargs={"pk": str(self.case.pk)})
            + "?template="
            + str(self.letter_template.id)
            + "&text="
            + text
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("preview" in response.json())
        preview = response.json()["preview"]
        for html_tag in ["<style>", "</style>"]:
            self.assertTrue(html_tag in preview)
        self.assertTrue(text in preview)

    def test_get_document_preview_without_text_success(self):
        url = (
            reverse("cases:generated_documents:preview", kwargs={"pk": str(self.case.pk)})
            + "?template="
            + str(self.letter_template.id)
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
        self.assertEqual(body["errors"], [strings.Cases.GeneratedDocuments.MISSING_TEMPLATE])

    @mock.patch("api.cases.generated_documents.helpers.generate_preview")
    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
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


class GetGeneratedDocumentsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.letter_template = self.create_letter_template(name="SIEL", case_types=[CaseTypeEnum.SIEL.id])
        self.case = self.create_standard_application_case(self.organisation)
        self.generated_case_document = self.create_generated_case_document(self.case, template=self.letter_template)
        self.url = reverse("cases:generated_documents:generated_documents", kwargs={"pk": str(self.case.pk)},)

    def test_get_generated_document_gov_user_success(self):
        url = reverse(
            "cases:generated_documents:generated_document",
            kwargs={"pk": str(self.case.pk), "dpk": str(self.generated_case_document.id)},
        )

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["template"], str(self.letter_template.id))
        self.assertEqual(response.json()["text"], self.generated_case_document.text)

    @mock.patch("api.cases.generated_documents.views.delete_exporter_notifications")
    def test_get_generated_documents_exporter_user_success(self, mock_delete):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.generated_case_document.id))
        self.assertEqual(response_data[0]["name"], self.generated_case_document.name)
        mock_delete.assert_called_once()

    def test_get_generated_documents_gov_user_success(self):
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.generated_case_document.id))
        self.assertEqual(response_data[0]["name"], self.generated_case_document.name)

    def test_get_generated_documents_not_visible_to_exporter_gov_user_success(self):
        document = self.create_generated_case_document(
            self.case, template=self.letter_template, visible_to_exporter=False
        )

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 2)
        self.assertTrue(str(document.pk) in [doc["id"] for doc in response_data])

    def test_get_generated_documents_not_visible_to_exporter_exporter_user_success(self):
        document = self.create_generated_case_document(
            self.case, template=self.letter_template, visible_to_exporter=False
        )

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertFalse(str(document.pk) in [doc["id"] for doc in response_data])
