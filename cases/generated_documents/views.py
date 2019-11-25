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
from documents.helpers import DocumentOperation
from letter_templates.helpers import get_preview
from lite_content.lite_api.cases import GeneratedDocumentsEndpoint
from lite_content.lite_api.letter_templates import LetterTemplatesPage


class GeneratedDocuments(APIView):
    authentication_classes = (GovAuthentication,)
    queryset = GeneratedDocument.objects.all()

    def _fetch_generated_document_data(self, request_params, pk):
        if "template" not in request_params:
            return JsonResponse({"errors": [LetterTemplatesPage.MISSING_TEMPLATE]}, status=status.HTTP_400_BAD_REQUEST)

        tpk = request_params["template"]
        self.case = get_case(pk)
        self.template = get_letter_template_for_case(tpk, self.case)
        self.html = get_preview(template=self.template, case=self.case)

        if "error" in self.html:
            return JsonResponse(data={"errors": [self.html["error"]]}, status=status.HTTP_400_BAD_REQUEST)

        return None

    def get(self, request, pk):
        """
        Get a preview of the document to be generated
        """
        error_response = self._fetch_generated_document_data(request.GET, pk)
        if error_response:
            return error_response

        return JsonResponse(data={"preview": self.html}, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request, pk):
        """
        Create a generated document
        """

        error_response = self._fetch_generated_document_data(request.data, pk)
        if error_response:
            return error_response

        try:
            pdf = html_to_pdf(request, self.html, self.template.layout.filename)
        except Exception:  # noqa
            return JsonResponse(
                {"errors": [GeneratedDocumentsEndpoint.PDF_ERROR]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        s3_key = DocumentOperation().generate_s3_key(self.template.name, "pdf")
        document_name = f"{self.template.name}-{s3_key[:len(self.template.name) + 5]}.pdf"

        generated_doc = GeneratedDocument.objects.create(
            name=document_name,
            user=request.user,
            s3_key=s3_key,
            virus_scanned_at=timezone.now(),
            safe=True,
            type=CaseDocumentType.GENERATED,
            case=self.case,
            template=self.template,
        )

        # Generate timeline entry
        case_activity = {
            "activity_type": CaseActivityType.GENERATE_CASE_DOCUMENT,
            "file_name": document_name,
            "template": self.template.name,
        }
        case_activity = CaseActivity.create(case=self.case, user=request.user, **case_activity)

        try:
            DocumentOperation().upload_bytes_file(raw_file=pdf, s3_key=".pdf")
        except Exception:  # noqa
            case_activity.delete()
            generated_doc.delete()
            return JsonResponse(
                {"errors": [GeneratedDocumentsEndpoint.UPLOAD_ERROR]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return JsonResponse(data={"generated_document": str(generated_doc.id)}, status=status.HTTP_201_CREATED)
