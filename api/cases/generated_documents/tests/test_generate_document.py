import os, io
import re

from datetime import datetime
from unittest import mock
from api.audit_trail.enums import AuditType
from parameterized import parameterized

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings

from rest_framework import status
from rest_framework.reverse import reverse
from tempfile import NamedTemporaryFile
from PyPDF2 import PdfFileReader
from api.audit_trail.serializers import AuditSerializer

from api.audit_trail.models import Audit
from api.applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from api.cases.enums import CaseTypeEnum, AdviceType
from api.cases.generated_documents.helpers import html_to_pdf
from api.cases.tests.factories import FinalAdviceFactory
from api.letter_templates.helpers import generate_preview, DocumentPreviewError
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.goods.tests.factories import GoodFactory
from api.cases.generated_documents.signing import sign_pdf
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import GoodOnLicenceFactory, StandardLicenceFactory
from api.staticdata.decisions.models import Decision
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.report_summaries.models import ReportSummarySubject, ReportSummaryPrefix
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient
from api.users.models import ExporterNotification


def get_tag(html, tag, id):
    lines = []
    all_lines = html.split("\n")
    for index, line in enumerate(all_lines):
        match = re.search(f'<{tag} id="{id}"', line)
        if match:
            # element spans multiple lines
            if f"</{tag}>" not in line:
                index = index + 1
                while f"</{tag}>" not in all_lines[index]:
                    lines.append(all_lines[index])
                    index = index + 1
            else:
                lines.append(line)
            break

    return lines


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
    @mock.patch("api.cases.generated_documents.views.s3_operations.generate_s3_key")
    def test_generate_document_success(self, generate_s3_key_func, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        generate_s3_key_func.return_value = "fake-s3-key.pdf"
        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        html_to_pdf_func.assert_called_once()
        upload_bytes_file_func.assert_has_calls(
            [
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.css"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.html"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.pdf"),
            ]
        )
        self.assertEqual(GeneratedCaseDocument.objects.count(), 1)
        self.assertEqual(
            ExporterNotification.objects.filter(
                user_id=self.exporter_user.pk,
                content_type=self.content_type,
                organisation=self.exporter_user.organisation,
            ).count(),
            1,
        )

    @parameterized.expand(
        [
            (AdviceType.INFORM, "created an inform letter."),
            (AdviceType.REFUSE, "created a refusal letter."),
            (AdviceType.NO_LICENCE_REQUIRED, "created a 'no licence required' letter."),
        ],
    )
    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_audit(self, advicetype, expected_text, upload_bytes_file_func, html_to_pdf_func):
        self.data["advice_type"] = advicetype
        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check add audit
        self.assertEqual(Audit.objects.all().count(), 2)

        audit = Audit.objects.all().first()
        self.assertEqual(AuditType(audit.verb), AuditType.GENERATE_DECISION_LETTER)
        year_now = datetime.now().year
        self.assertEqual(
            audit.payload,
            {"decision": advicetype, "case_reference": f"GBSIEL/{year_now}/0000001/P"},
        )

        audit_text = AuditSerializer(audit).data["text"]
        self.assertEqual(audit_text, expected_text)

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    @mock.patch("api.cases.generated_documents.views.sign_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.generate_s3_key")
    def test_generate_document_with_signature_success(
        self, generate_s3_key_func, sign_pdf_func, upload_bytes_file_func, html_to_pdf_func
    ):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        generate_s3_key_func.return_value = "fake-s3-key.pdf"
        sign_pdf_func.return_value = None
        template = self.create_letter_template(case_types=[CaseTypeEnum.SIEL.id], digital_signature=True)
        self.data["template"] = str(template.id)

        url = reverse("cases:generated_documents:generated_documents", kwargs={"pk": str(self.case.pk)})
        response = self.client.post(url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        html_to_pdf_func.assert_called_once()
        upload_bytes_file_func.assert_has_calls(
            [
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.css"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.html"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.pdf"),
            ]
        )
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
    @mock.patch("api.cases.generated_documents.views.s3_operations.generate_s3_key")
    def test_generate_document_with_hidden_template_success(
        self, generate_s3_key_func, upload_bytes_file_func, html_to_pdf_func
    ):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        generate_s3_key_func.return_value = "fake-s3-key.pdf"
        template = self.create_letter_template(case_types=[CaseTypeEnum.SIEL.id], visible_to_exporter=False)
        self.data["template"] = str(template.id)

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        html_to_pdf_func.assert_called_once()
        upload_bytes_file_func.assert_has_calls(
            [
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.css"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.html"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.pdf"),
            ]
        )
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
    @mock.patch("api.cases.generated_documents.views.s3_operations.generate_s3_key")
    def test_generate_decision_document_success(
        self,
        advice_type,
        appeal_deadline_set,
        generate_s3_key_func,
        upload_bytes_file_func,
        html_to_pdf_func,
    ):
        application = self.case
        licence = None
        if advice_type == AdviceType.APPROVE:
            licence = StandardLicenceFactory(case=self.case, status=LicenceStatus.DRAFT)

        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        generate_s3_key_func.return_value = "fake-s3-key.pdf"
        self.data["visible_to_exporter"] = True

        self.data["advice_type"] = advice_type

        self.assertIsNone(application.appeal_deadline)

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        application.refresh_from_db()
        assert bool(application.appeal_deadline) == appeal_deadline_set

        upload_bytes_file_func.assert_has_calls(
            [
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.css"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.html"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.pdf"),
            ]
        )
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
    @mock.patch("api.cases.generated_documents.views.s3_operations.generate_s3_key")
    def test_regenerate_decision_document_success(
        self,
        template_name,
        decisions,
        appeal_deadline_set,
        generate_s3_key_func,
        upload_bytes_file_func,
        html_to_pdf_func,
    ):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        generate_s3_key_func.return_value = "fake-s3-key.pdf"

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

        upload_bytes_file_func.assert_has_calls(
            [
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.css"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.html"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.pdf"),
            ]
        )

        self.assertEqual(GeneratedCaseDocument.objects.filter(template=template).count(), 1)

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    @mock.patch("api.cases.generated_documents.views.s3_operations.generate_s3_key")
    def test_generate_licence_document_success(self, generate_s3_key_func, upload_bytes_file_func, html_to_pdf_func):
        licence = StandardLicenceFactory(case=self.case, status=LicenceStatus.DRAFT)
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        generate_s3_key_func.return_value = "fake-s3-key.pdf"
        self.data["visible_to_exporter"] = True
        self.data["advice_type"] = AdviceType.APPROVE

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        html_to_pdf_func.assert_called_once()
        upload_bytes_file_func.assert_has_calls(
            [
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.css"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.html"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.pdf"),
            ]
        )
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
    @mock.patch("api.cases.generated_documents.views.s3_operations.generate_s3_key")
    def test_generate_new_licence_document_success(
        self, generate_s3_key_func, upload_bytes_file_func, html_to_pdf_func
    ):
        licence = StandardLicenceFactory(case=self.case, status=LicenceStatus.DRAFT)
        self.create_generated_case_document(
            self.case, self.letter_template, advice_type=AdviceType.APPROVE, licence=licence, visible_to_exporter=False
        )

        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        generate_s3_key_func.return_value = "fake-s3-key.pdf"

        self.data["visible_to_exporter"] = True
        self.data["advice_type"] = AdviceType.APPROVE

        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        upload_bytes_file_func.assert_has_calls(
            [
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.css"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.html"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.pdf"),
            ]
        )
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
    @mock.patch("api.cases.generated_documents.views.s3_operations.generate_s3_key")
    def test_generate_document_when_html_to_pdf_throws_error_failure(
        self, generate_s3_key_func, upload_bytes_file_func, html_to_pdf_func
    ):
        html_to_pdf_func.side_effect = Exception("Failed to convert html to pdf")
        generate_s3_key_func.return_value = "fake-s3-key.pdf"

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
        upload_bytes_file_func.assert_has_calls(
            [
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.css"),
                mock.call(raw_file=mock.ANY, s3_key="fake-s3-key.html"),
            ],
            any_order=True,
        )

    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_when_s3_throws_error_failure(self, upload_bytes_file_func, html_to_pdf_func):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.side_effect = [None, None, Exception("Failed to upload document")]

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

    @mock.patch("api.cases.generated_documents.helpers.generate_preview")
    def test_get_document_preview_raises_error(self, mock_generate_preview):
        mock_generate_preview.side_effect = DocumentPreviewError("error")
        text = "Sample"
        url = (
            reverse("cases:generated_documents:preview", kwargs={"pk": str(self.case.pk)})
            + "?template="
            + str(self.letter_template.id)
            + "&text="
            + text
        )
        with self.assertRaises(AttributeError) as e:
            response = self.client.get(url, **self.gov_headers)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(e.exception, "Failed to get preview")

    @mock.patch("api.cases.generated_documents.views.get_generated_document_data")
    @mock.patch("api.cases.generated_documents.views.html_to_pdf")
    @mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file")
    def test_generate_document_post_raises_attributeerror(
        self, upload_bytes_file_func, html_to_pdf_func, mock_gen_doc_data
    ):
        html_to_pdf_func.return_value = None
        upload_bytes_file_func.return_value = None
        mock_gen_doc_data.side_effect = AttributeError("error")

        with self.assertRaises(AttributeError) as e:
            response = self.client.post(self.url, **self.gov_headers, data=self.data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(e.exception, "Failed to get preview")

    def test_licence_document_shows_correct_cles(self):
        """
        Test to ensure licence document shows CLEs for the products assessed as part of this application.
        This is usually the case but can be different if the underlying Good is re-used in multiple applications.

        In this test we create two applications that reuse the same underlying Good but in each application
        this is assessed with different set of CLEs. Because of the way we record CLEs on the Good model
        it will retain previous assessments as well (unlike GoodOnApplication which contains assessments
        for that application).

        Test generates licence document and ensures it contains CLEs assessed for this application.
        """
        application1 = StandardApplicationFactory(organisation=self.organisation)
        good1 = GoodFactory(organisation=self.organisation)
        good_on_application1 = GoodOnApplicationFactory(good=good1, application=application1, quantity=10, value=500)
        regime_entry = RegimeEntry.objects.first()
        report_summary_prefix = ReportSummaryPrefix.objects.first()
        report_summary_subject = ReportSummarySubject.objects.first()
        data = [
            {
                "id": good_on_application1.id,
                "control_list_entries": ["ML3a", "ML15d", "ML9a"],
                "regime_entries": [regime_entry.id],
                "report_summary_prefix": report_summary_prefix.id,
                "report_summary_subject": report_summary_subject.id,
                "is_good_controlled": True,
                "comment": "some comment",
                "report_summary": "some string we expect to be overwritten",
                "is_ncsc_military_information_security": True,
            }
        ]
        assessment_url = reverse("assessments:make_assessments", kwargs={"case_pk": application1.id})
        response = self.client.put(assessment_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        good_on_application1.refresh_from_db()

        all_cles = [cle.rating for cle in good_on_application1.control_list_entries.all()]
        assert sorted(all_cles) == sorted(["ML3a", "ML9a", "ML15d"])

        FinalAdviceFactory(user=self.gov_user, case=application1, good=good1, type=AdviceType.APPROVE)

        licence = StandardLicenceFactory(case=application1, status=LicenceStatus.DRAFT)
        GoodOnLicenceFactory(
            good=good_on_application1,
            quantity=good_on_application1.quantity,
            value=good_on_application1.value,
            licence=licence,
        )

        # Create another application and reuse the same good
        application2 = StandardApplicationFactory(organisation=self.organisation)
        good_on_application2 = GoodOnApplicationFactory(good=good1, application=application2, quantity=20, value=1000)

        data[0]["id"] = good_on_application2.id
        data[0]["control_list_entries"] = ["ML5d", "ML2a", "ML18a"]
        assessment_url = reverse("assessments:make_assessments", kwargs={"case_pk": application2.id})
        response = self.client.put(assessment_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        good_on_application2.refresh_from_db()

        all_cles = [cle.rating for cle in good_on_application2.control_list_entries.all()]
        assert sorted(all_cles) == sorted(["ML5d", "ML2a", "ML18a"])

        # As this is reused this will have CLEs from both assessments
        good1.refresh_from_db()
        all_cles = [cle.rating for cle in good1.control_list_entries.all()]
        assert sorted(all_cles) == sorted(["ML3a", "ML9a", "ML15d", "ML5d", "ML2a", "ML18a"])

        # Generate licence document (only preview is enough for this test)
        url = (
            reverse("cases:generated_documents:preview", kwargs={"pk": str(application1.id)})
            + "?template="
            + str(self.letter_template.id)
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        preview = response.json()["preview"]

        cle_lines = get_tag(preview, "td", "row-1-control-list-entries")
        actual_cles = "".join(item.strip() for item in cle_lines)

        all_cles = [cle.rating for cle in good_on_application1.control_list_entries.all()]
        assert sorted(all_cles) == sorted(actual_cles.split(","))

        value_element = get_tag(preview, "td", "row-1-value")
        value_element = "".join(value_element)
        self.assertIn(f"£{str(good_on_application1.value)}", value_element)

        quantity_element = get_tag(preview, "td", "row-1-quantity")
        quantity_element = "".join(quantity_element)
        self.assertIn(f"{good_on_application1.quantity} Items", quantity_element)


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
            ("inform_letter", "Inform letter"),
        ],
    )
    @override_settings(
        DOCUMENT_SIGNING_ENABLED=True,
        P12_CERTIFICATE="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",  # /PS-IGNORE
        CERTIFICATE_PASSWORD="testing",
        SIGNING_EMAIL="test@example.com",  # /PS-IGNORE
    )
    def test_pdf_titles(self, layout, title):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        html = generate_preview(layout=layout, case=case, text="")
        pdf = html_to_pdf(html, layout, None)
        document_signing_data = case.get_application_manifest().document_signing
        pdf = sign_pdf(
            pdf,
            document_signing_data["signing_reason"],
            document_signing_data["location"],
            document_signing_data["image_name"],
        )

        with io.BytesIO(pdf) as open_pdf_file:
            reader = PdfFileReader(open_pdf_file)
            meta = reader.getDocumentInfo()
            self.assertEqual(meta.title, f"{title} {case.reference_code}")

    @override_settings(
        DOCUMENT_SIGNING_ENABLED=True,
        P12_CERTIFICATE="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",  # /PS-IGNORE
        CERTIFICATE_PASSWORD="testing",
        SIGNING_EMAIL="test@example.com",  # /PS-IGNORE
        SIGNING_LOCATION="test location",
        SIGNING_REASON="test signing reason",
    )
    def test_cell_truncation(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        FinalAdviceFactory(
            case=case,
            good=case.goods.get().good,
            proviso="".join(f"test {i}\n" for i in range(200)),
            user=self.gov_user,
        )
        html = generate_preview(layout="siel", case=case, text="")
        pdf = html_to_pdf(html, "siel", None)

        with io.BytesIO(pdf) as open_pdf_file:
            reader = PdfFileReader(open_pdf_file)
            # This uses the number of pages as a rough way of testing that the proviso cell hasn't been truncated.
            # Ideally we'd do something a bit more explicit around the text that's rendered on the PDF but PdfFileReader
            # seems to have difficulty extracting out the text properly
            self.assertEqual(reader.getNumPages(), 7)
