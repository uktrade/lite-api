from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView

from cases.enums import CaseDocumentState
from cases.generated_documents.helpers import html_to_pdf, get_letter_template_for_case
from cases.generated_documents.models import GeneratedCaseDocument
from cases.libraries.activity_types import CaseActivityType
from cases.libraries.get_case import get_case
from cases.models import CaseActivity
from conf.authentication import GovAuthentication
from documents.libraries import s3_operations
from letter_templates.helpers import markdown_to_html, generate_preview
from lite_content.lite_api.cases import GeneratedDocumentsEndpoint
from lite_content.lite_api.letter_templates import LetterTemplatesPage


def _get_generated_document_data(request_params, pk):
    tpk = request_params.get("template")
    if not tpk:
        return LetterTemplatesPage.MISSING_TEMPLATE, None, None, None, None

    text = request_params.get("text")
    if not text:
        return "Missing text", None, None, None, None
    text = markdown_to_html(text)

    case = get_case(pk)
    template = get_letter_template_for_case(tpk, case)
    document_html = generate_preview(layout=template.layout.filename, text=text, case=case)

    if "error" in document_html:
        return document_html["error"], None, None, None, None

    return None, case, template, document_html, text


class GeneratedDocuments(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def post(self, request, pk):
        """
        Create a generated document
        """
        error, case, template, document_html, text = _get_generated_document_data(request.data, pk)

        if error:
            return JsonResponse(data={"errors": [error]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pdf = html_to_pdf(request, document_html, template.layout.filename)
        except Exception:  # noqa
            return JsonResponse(
                {"errors": [GeneratedDocumentsEndpoint.PDF_ERROR]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        s3_key = s3_operations.generate_s3_key(template.name, "pdf")
        # base the document name on the template name and a portion of the UUID generated for the s3 key
        document_name = f"{s3_key[:len(template.name) + 6]}.pdf"

        try:
            with transaction.atomic():
                generated_doc = GeneratedCaseDocument.objects.create(
                    name=document_name,
                    user=request.user,
                    s3_key=s3_key,
                    virus_scanned_at=timezone.now(),
                    safe=True,
                    type=CaseDocumentState.GENERATED,
                    case=case,
                    template=template,
                    text=text,
                )

                # Generate timeline entry
                case_activity = {
                    "activity_type": CaseActivityType.GENERATE_CASE_DOCUMENT,
                    "file_name": document_name,
                    "template": template.name,
                }
                CaseActivity.create(case=case, user=request.user, **case_activity)

                s3_operations.upload_bytes_file(raw_file=pdf, s3_key=s3_key)
        except Exception:  # noqa
            return JsonResponse(
                {"errors": [GeneratedDocumentsEndpoint.UPLOAD_ERROR]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return JsonResponse(data={"generated_document": str(generated_doc.id)}, status=status.HTTP_201_CREATED)


class GeneratedDocumentPreview(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Get a preview of the document to be generated
        """
        error, _, _, document_html, _ = _get_generated_document_data(request.GET, pk)

        if error:
            return JsonResponse(data={"errors": [error]}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data={"preview": document_html}, status=status.HTTP_200_OK)
