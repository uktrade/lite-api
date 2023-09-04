import os, io

from unittest import mock
from api.audit_trail.enums import AuditType
from parameterized import parameterized

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse
from tempfile import NamedTemporaryFile
from PyPDF2 import PdfFileReader

from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum, AdviceType
from api.cases.generated_documents.helpers import html_to_pdf
from api.letter_templates.helpers import generate_preview
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.licences.enums import LicenceStatus
from api.staticdata.decisions.models import Decision
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
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
                user_id=self.exporter_user.pk,
                content_type=self.content_type,
                organisation=self.exporter_user.organisation,
            ).count(),
            1,
        )

    @parameterized.expand([AdviceType.INFORM, AdviceType.REFUSE, AdviceType.NO_LICENCE_REQUIRED])
    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_audit(self, advicetype, upload_bytes_file_func, html_to_pdf_func):
        self.data["advice_type"] = advicetype
        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check add audit
        self.assertEqual(Audit.objects.all().count(), 2)

        audit = Audit.objects.all().first()
        self.assertEqual(AuditType(audit.verb), AuditType.GENERATE_DECISION_LETTER)
        self.assertEqual(
            audit.payload,
            {"decision": advicetype, "case_reference": "GBSIEL/2023/0000001/P"},
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
                user_id=self.exporter_user.pk,
                content_type=self.content_type,
                organisation=self.exporter_user.organisation,
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
                user_id=self.exporter_user.pk,
                content_type=self.content_type,
                organisation=self.exporter_user.organisation,
            ).count(),
            0,
        )
        self.assertEqual(GeneratedCaseDocument.objects.get().visible_to_exporter, False)

    @parameterized.expand(
        (
            (AdviceType.NO_LICENCE_REQUIRED, False),
            (AdviceType.APPROVE, False),
            (AdviceType.REFUSE, True),
        ),
    )
    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_decision_document_success(
        self, advice_type, appeal_deadline_set, upload_bytes_file_func, html_to_pdf_func
    ):
        application = self.case
        licence = None
        if advice_type == AdviceType.APPROVE:
            licence = self.create_licence(self.case, status=LicenceStatus.DRAFT)

        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        self.data["visible_to_exporter"] = True

        self.data["advice_type"] = advice_type

        self.assertIsNone(application.appeal_deadline)

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        application.refresh_from_db()
        assert bool(application.appeal_deadline) == appeal_deadline_set

        upload_bytes_file_func.assert_called_once()
        self.assertEqual(GeneratedCaseDocument.objects.filter(advice_type=advice_type, licence=licence).count(), 1)
        # Ensure decision documents are hidden until complete
        self.assertEqual(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk,
                content_type=self.content_type,
                organisation=self.exporter_user.organisation,
            ).count(),
            0,
        )

    @parameterized.expand(
        (
            ("SIEL NLR", [AdviceType.NO_LICENCE_REQUIRED], False),
            ("SIEL Approval", [AdviceType.APPROVE, AdviceType.PROVISO], False),
            ("SIEL Refusal", [AdviceType.REFUSE], True),
        ),
    )
    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_regenerate_decision_document_success(
        self, template_name, decisions, appeal_deadline_set, upload_bytes_file_func, html_to_pdf_func
    ):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None

        self.case.status = CaseStatus.objects.get(status=CaseStatusEnum.FINALISED)
        self.case.save()

        application = self.case
        decisions = Decision.objects.filter(name__in=decisions)
        template = self.create_letter_template(
            name=template_name, case_types=[CaseTypeEnum.SIEL.id], decisions=decisions
        )

        self.assertIsNone(application.appeal_deadline)

        self.data = {"template": str(template.id), "text": "sample", "visible_to_exporter": True}
        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        application.refresh_from_db()
        assert bool(application.appeal_deadline) == appeal_deadline_set

        upload_bytes_file_func.assert_called_once()
        self.assertEqual(GeneratedCaseDocument.objects.filter(template=template).count(), 1)

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
                user_id=self.exporter_user.pk,
                content_type=self.content_type,
                organisation=self.exporter_user.organisation,
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
                user_id=self.exporter_user.pk,
                content_type=self.content_type,
                organisation=self.exporter_user.organisation,
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
                user_id=self.exporter_user.pk,
                content_type=self.content_type,
                organisation=self.exporter_user.organisation,
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
                user_id=self.exporter_user.pk,
                content_type=self.content_type,
                organisation=self.exporter_user.organisation,
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

        with self.assertRaises(AttributeError) as e:
            self.client.get(url, **self.gov_headers)
            self.assertEqual(e.exception, strings.Cases.GeneratedDocuments.MISSING_TEMPLATE)

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

        with self.assertRaises(AttributeError) as e:
            self.client.get(url, **self.gov_headers)
            self.assertEqual(e.exception, "Failed to get preview")

        html_to_pdf_func.assert_not_called()
        upload_bytes_file_func.assert_not_called()

    def test_get_document_preview_when_get_html_contains_error_string(self):
        url = (
            reverse("cases:generated_documents:preview", kwargs={"pk": str(self.case.pk)})
            + "?template="
            + str(self.letter_template.id)
            + "&text=This text contains the string - error"
        )

        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_presence_of_css_files_for_document_templates(self):
        expected = ["siel.css", "siel_preview.css", "nlr.css", "refusal.css"]
        css_files = os.listdir(settings.CSS_ROOT)
        self.assertTrue(set(expected).issubset(css_files))

    def test_generating_siel_licence_pdf_with_css(self):
        resp = html_to_pdf("<div>Hello World !!</div>", "siel", None)
        with NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_file:
            tmp_file.write(resp)

        resp = html_to_pdf("<div>Hello World !!</div>", "siel_preview", None)
        with NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_file:
            tmp_file.write(resp)


class GetGeneratedDocumentsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.letter_template = self.create_letter_template(name="SIEL", case_types=[CaseTypeEnum.SIEL.id])
        self.case = self.create_standard_application_case(self.organisation)
        self.generated_case_document = self.create_generated_case_document(self.case, template=self.letter_template)
        self.url = reverse(
            "cases:generated_documents:generated_documents",
            kwargs={"pk": str(self.case.pk)},
        )

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


class TestGeneratedTemplatePDF(DataTestClient):
    @parameterized.expand(
        [
            ("application_form", "Application form"),
            ("nlr", "No licence required letter"),
            ("refusal", "Refusal letter"),
            ("siel", "Standard individual export licence"),
            ("inform_letter", ""),
        ],
    )
    def test_pdf_titles(self, temp, title):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        html = generate_preview(layout=temp, case=case, text="")
        pdf = html_to_pdf(html, temp, None)
        with io.BytesIO(pdf) as open_pdf_file:
            reader = PdfFileReader(open_pdf_file)
            meta = reader.getDocumentInfo()
            self.assertEqual(meta.title, f"{title} {case.reference_code}")
