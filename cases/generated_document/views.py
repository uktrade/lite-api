from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView

from cases.enums import CaseDocumentType
from cases.generated_document.helpers import html_to_pdf
from cases.generated_document.models import GeneratedDocument
from cases.libraries.get_case import get_case
from conf.authentication import GovAuthentication
from documents.helpers import DocumentOperation
from letter_templates.helpers import generate_preview, paragraphs_to_markdown
from letter_templates.models import LetterTemplate


class GeneratedDocuments(APIView):
    authentication_classes = (GovAuthentication,)
    queryset = GeneratedDocument.objects.all()

    def post(self, request, pk):
        # TODO Add validation
        case = get_case(pk)
        template = LetterTemplate.objects.get(id=request.data['template'])

        paragraphs = [paragraph.text for paragraph in template.letter_paragraphs.all()]
        paragraphs = paragraphs_to_markdown(paragraphs)
        html = generate_preview(template.layout.filename, paragraphs)

        pdf = html_to_pdf(html)
        s3_key = DocumentOperation().upload_bytes_file(raw_file=pdf, file_extension=".pdf")

        generated_doc = GeneratedDocument.objects.create(
            name=s3_key,
            user=request.user,
            s3_key=s3_key,
            virus_scanned_at=timezone.now(),
            safe=True,
            type=CaseDocumentType.GENERATED,
            case=case,
            template=template,
        )

        return JsonResponse(
            data={"generated_document": str(generated_doc.id)},
            status=status.HTTP_201_CREATED
        )
