from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView

from cases.enums import CaseDocumentType
from cases.generated_document.helpers import html_to_pdf, get_letter_template
from cases.generated_document.models import GeneratedDocument
from cases.libraries.activity_types import CaseActivityType
from cases.libraries.get_case import get_case
from cases.models import CaseActivity
from conf.authentication import GovAuthentication
from documents.helpers import DocumentOperation
from letter_templates.helpers import get_preview
from letter_templates.models import LetterTemplate


class GeneratedDocuments(APIView):
    authentication_classes = (GovAuthentication,)
    queryset = GeneratedDocument.objects.all()

    def _fetch_generated_document_data(self, pk, tpk):
        self.case = get_case(pk)
        self.template = get_letter_template(id=tpk, case_type=self.case.type)
        self.html = get_preview(template=self.template, case=self.case)

    def get(self, request, pk):
        """
        Get a preview of the document to be generated
        """
        # TODO Add validation
        tpk = request.GET["template"]
        self._fetch_generated_document_data(pk, tpk)
        return JsonResponse(data={"preview": self.html}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        """
        Create a generated document
        """
        # TODO Add validation
        tpk = request.data["template"]
        self._fetch_generated_document_data(pk, tpk)
        pdf = html_to_pdf(self.html, self.template.layout.name)
        s3_key = DocumentOperation().upload_bytes_file(raw_file=pdf, file_extension=".pdf")
        document_name = self.template.name + "-" + s3_key[:4]
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
        CaseActivity.create(case=self.case, user=request.user, **case_activity)

        return JsonResponse(data={"generated_document": str(generated_doc.id)}, status=status.HTTP_201_CREATED)
