from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import CaseDocumentState
from cases.generated_documents.helpers import html_to_pdf, get_generated_document_data
from cases.generated_documents.models import GeneratedCaseDocument
from cases.generated_documents.serializers import GeneratedCaseDocumentGovSerializer
from conf.authentication import GovAuthentication
from documents.libraries import s3_operations
from lite_content.lite_api.cases import GeneratedDocumentsEndpoint


class GeneratedDocument(generics.RetrieveAPIView):
    authentication_classes = (GovAuthentication,)
    queryset = GeneratedCaseDocument.objects.all()
    serializer_class = GeneratedCaseDocumentGovSerializer


class GeneratedDocuments(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def post(self, request, pk):
        """
        Create a generated document
        """
        try:
            document = get_generated_document_data(request.data, pk)
        except AttributeError as e:
            return JsonResponse(data={"errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pdf = html_to_pdf(request, document.document_html, document.template.layout.filename)
        except Exception:  # noqa
            return JsonResponse(
                {"errors": [GeneratedDocumentsEndpoint.PDF_ERROR]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        s3_key = s3_operations.generate_s3_key(document.template.name, "pdf")
        # base the document name on the template name and a portion of the UUID generated for the s3 key
        document_name = f"{s3_key[:len(document.template.name) + 6]}.pdf"

        try:
            with transaction.atomic():
                generated_doc = GeneratedCaseDocument.objects.create(
                    name=document_name,
                    user=request.user,
                    s3_key=s3_key,
                    virus_scanned_at=timezone.now(),
                    safe=True,
                    type=CaseDocumentState.GENERATED,
                    case=document.case,
                    template=document.template,
                    text=document.text,
                )

                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.GENERATE_CASE_DOCUMENT,
                    action_object=generated_doc,
                    target=document.case,
                    payload={'file_name': document_name, 'template': document.template.name}
                )

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
        try:
            document = get_generated_document_data(request.GET, pk)
        except AttributeError as e:
            return JsonResponse(data={"errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data={"preview": document.document_html}, status=status.HTTP_200_OK)
