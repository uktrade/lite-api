from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView

from cases.enums import CaseDocumentType
from cases.generated_documents.helpers import html_to_pdf, get_letter_template_for_case
from cases.generated_documents.models import GeneratedDocument
from cases.libraries.activity_types import CaseActivityType
from cases.libraries.get_case import get_case
from cases.models import CaseActivity
from conf.authentication import GovAuthentication
from documents.libraries import s3_operations
from letter_templates.helpers import get_preview
from lite_content.lite_api.cases import GeneratedDocumentsEndpoint
from lite_content.lite_api.letter_templates import LetterTemplatesPage


def _get_generated_document_data(request_params, pk):
    tpk = request_params.get("template")
    if not tpk:
        return LetterTemplatesPage.MISSING_TEMPLATE, None, None, None

    case = get_case(pk)
    template = get_letter_template_for_case(tpk, case)
    document_html = get_preview(template=template, case=case)

    if "error" in document_html:
        return document_html["error"], None, None, None

    return None, case, template, document_html


class GeneratedDocuments(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def post(self, request, pk):
        """
        Create a generated document
        """

        error, case, template, document_html = _get_generated_document_data(request.data, pk)

        if error:
            return JsonResponse(data={"errors": [error]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pdf = html_to_pdf(request, document_html, template.layout.filename)
        except Exception:  # noqa
            return JsonResponse(
                {"errors": [GeneratedDocumentsEndpoint.PDF_ERROR]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        s3_key = s3_operations.generate_s3_key(template.name, "pdf")
        document_name = f"{s3_key[:len(template.name) + 6]}.pdf"

        generated_doc = GeneratedDocument.objects.create(
            name=document_name,
            user=request.user,
            s3_key=s3_key,
            virus_scanned_at=timezone.now(),
            safe=True,
            type=CaseDocumentType.GENERATED,
            case=case,
            template=template,
        )

        # Generate timeline entry
        case_activity = {
            "activity_type": CaseActivityType.GENERATE_CASE_DOCUMENT,
            "file_name": document_name,
            "template": template.name,
        }
        case_activity = CaseActivity.create(case=case, user=request.user, **case_activity)

        try:
            s3_operations.upload_bytes_file(raw_file=pdf, s3_key=s3_key)
        except Exception:  # noqa
            case_activity.delete()
            generated_doc.delete()
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

        error, case, template, document_html = _get_generated_document_data(request.GET, pk)

        if error:
            return JsonResponse(data={"errors": [error]}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data={"preview": document_html}, status=status.HTTP_200_OK)
