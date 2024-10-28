import os, io
import re

from datetime import datetime
from unittest import mock
from api.audit_trail.enums import AuditType
from parameterized import parameterized

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse
from tempfile import NamedTemporaryFile
from PyPDF2 import PdfFileReader
from api.audit_trail.serializers import AuditSerializer

from api.audit_trail.models import Audit
from api.applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from api.cases.models import LicenceDecision
from api.cases.enums import CaseTypeEnum, AdviceType, LicenceDecisionType
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
            licence = StandardLicenceFactory(case=self.case, status=LicenceStatus.DRAFT)

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
        licence = StandardLicenceFactory(case=self.case, status=LicenceStatus.DRAFT)
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

        licence_decision = LicenceDecision.objects.get()
        self.assertEqual(licence_decision.case, self.case.get_case())
        self.assertEqual(licence_decision.decision, LicenceDecisionType.ISSUED)
        self.assertEqual(licence_decision.licence, licence)

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
        licence = StandardLicenceFactory(case=self.case, status=LicenceStatus.DRAFT)
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
    def test_pdf_titles(self, temp, title):
        # Make sure this setting is True
        settings.DOCUMENT_SIGNING_ENABLED = True

        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        html = generate_preview(layout=temp, case=case, text="")
        pdf = html_to_pdf(html, temp, None)
        pdf = sign_pdf(pdf)

        with io.BytesIO(pdf) as open_pdf_file:
            reader = PdfFileReader(open_pdf_file)
            meta = reader.getDocumentInfo()
            self.assertEqual(meta.title, f"{title} {case.reference_code}")
