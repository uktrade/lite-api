from collections import namedtuple

from weasyprint import CSS, HTML
from weasyprint.fonts import FontConfiguration

from cases.libraries.get_case import get_case
from conf.exceptions import NotFoundError
from letter_templates.helpers import get_css_location, generate_preview
from letter_templates.models import LetterTemplate
from lite_content.lite_api import strings
from parties.enums import PartyType
from parties.models import Party

font_config = FontConfiguration()
GeneratedDocumentPayload = namedtuple("GeneratedDocumentPayload", "case template document_html text")


def html_to_pdf(request, html: str, template_name: str):
    html = HTML(string=html, base_url=request.build_absolute_uri())
    css = CSS(filename=get_css_location(template_name), font_config=font_config)
    return html.write_pdf(stylesheets=[css], font_config=font_config)


def get_generated_document_data(request_params, pk):
    template_id = request_params.get("template")
    if not template_id:
        raise AttributeError(strings.Cases.GeneratedDocuments.MISSING_TEMPLATE)

    text = request_params.get("text")
    if not text:
        raise AttributeError(strings.Cases.GeneratedDocuments.MISSING_TEXT)

    additional_contact = request_params.get("addressee")
    if additional_contact:
        try:
            additional_contact = Party.objects.get(type=PartyType.ADDITIONAL_CONTACT, id=additional_contact)
        except Party.DoesNotExist:
            raise AttributeError(strings.Cases.GeneratedDocuments.INVALID_ADDRESSEE)

    case = get_case(pk)
    try:
        template = LetterTemplate.objects.get(pk=template_id, case_types=case.case_type)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": strings.Cases.GeneratedDocuments.LETTER_TEMPLATE_NOT_FOUND})
    document_html = generate_preview(
        layout=template.layout.filename, text=text, case=case, additional_contact=additional_contact
    )

    if "error" in document_html:
        raise AttributeError(document_html["error"])

    return GeneratedDocumentPayload(case=case, template=template, document_html=document_html, text=text)
