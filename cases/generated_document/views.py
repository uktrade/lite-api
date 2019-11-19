from datetime import datetime

from django.http import JsonResponse
from rest_framework.views import APIView

from cases.generated_document.helpers import html_to_pdf
from cases.generated_document.models import GeneratedDocument
from cases.generated_document.serialzers import GeneratedDocumentSerializer
from cases.libraries.get_case import get_case
from conf.authentication import GovAuthentication
from documents.helpers import DocumentOperation
from documents.models import Document
from letter_templates.helpers import generate_preview, paragraphs_to_markdown
from letter_templates.models import LetterTemplate


class GeneratedDocuments(APIView):
    authentication_classes = (GovAuthentication,)
    queryset = GeneratedDocument.objects.all()
    serializer_class = GeneratedDocumentSerializer

    def post(self, request, pk):
        # TODO Add validation
        case = get_case(pk)
        template = LetterTemplate.objects.get(id=request.data['template'])

        paragraphs = [paragraph.text for paragraph in template.letter_paragraphs.all()]
        paragraphs = paragraphs_to_markdown(paragraphs)
        html = generate_preview(template.layout.filename, paragraphs)

        pdf = html_to_pdf(html)
        s3_key = DocumentOperation().upload_bytes_file(raw_file=pdf, file_extension=".pdf")

        document = Document.objects.create(
            name=s3_key,
            s3_key=s3_key,
            virus_scanned_at=datetime.now(),
            safe=True
        )

        generated_doc = GeneratedDocument.objects.create(
            document=document,
            case=case,
            template=template,
            name=template.name+str(case.id)
        )

        return JsonResponse(data={"generated_document": generated_doc})
