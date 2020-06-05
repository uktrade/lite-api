from collections import namedtuple

from django.utils import timezone
from weasyprint import CSS, HTML
from weasyprint.fonts import FontConfiguration

from cases.enums import CaseDocumentState
from cases.libraries.get_case import get_case
from cases.models import CaseDocument
from conf.exceptions import NotFoundError
from documents.libraries import s3_operations
from letter_templates.helpers import get_css_location, generate_preview
from letter_templates.models import LetterTemplate
from lite_content.lite_api import strings

font_config = FontConfiguration()
GeneratedDocumentPayload = namedtuple("GeneratedDocumentPayload", "case template document_html text")


def html_to_pdf(html: str, template_name: str):
    html = HTML(string=html)
    css = CSS(filename=get_css_location(template_name), font_config=font_config)
    return html.write_pdf(stylesheets=[css], font_config=font_config)


def auto_generate_case_document(layout, case, document_name):
    html = generate_preview(layout=layout, text="", case=case)
    pdf = html_to_pdf(html, layout)
    s3_key = s3_operations.generate_s3_key(layout, "pdf")
    CaseDocument.objects.create(
        name=f"{document_name} - {timezone.now()}.pdf",
        s3_key=s3_key,
        virus_scanned_at=timezone.now(),
        safe=True,
        type=CaseDocumentState.AUTO_GENERATED,
        case=case,
        visible_to_exporter=False,
    )
    s3_operations.upload_bytes_file(raw_file=pdf, s3_key=s3_key)


def get_generated_document_data(request_params, pk):
    template_id = request_params.get("template")
    if not template_id:
        raise AttributeError(strings.Cases.MISSING_TEMPLATE)

    text = request_params.get("text")
    if not text:
        raise AttributeError(strings.Cases.MISSING_TEXT)

    case = get_case(pk)
    try:
        template = LetterTemplate.objects.get(pk=template_id, case_types=case.case_type)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": strings.Cases.LETTER_TEMPLATE_NOT_FOUND})
    document_html = generate_preview(layout=template.layout.filename, text=text, case=case)

    if "error" in document_html:
        raise AttributeError(document_html["error"])

    return GeneratedDocumentPayload(case=case, template=template, document_html=document_html, text=text)
