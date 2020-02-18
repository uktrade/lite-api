from collections import namedtuple

from weasyprint import CSS, HTML
from weasyprint.fonts import FontConfiguration

from cases.generated_documents.models import GeneratedCaseDocument
from cases.libraries.delete_notifications import delete_exporter_notifications
from cases.libraries.get_case import get_case
from cases.models import Case
from conf.exceptions import NotFoundError, PermissionDeniedError
from letter_templates.helpers import get_css_location, generate_preview, markdown_to_html
from letter_templates.models import LetterTemplate
from lite_content.lite_api import strings
from users.enums import UserType

font_config = FontConfiguration()
GeneratedDocumentPayload = namedtuple("GeneratedDocumentPayload", "case template document_html text")


def html_to_pdf(request, html: str, template_name: str):
    html = HTML(string=html, base_url=request.build_absolute_uri())
    css = CSS(filename=get_css_location(template_name), font_config=font_config)
    return html.write_pdf(stylesheets=[css], font_config=font_config)


def get_letter_templates_for_case(case):
    return LetterTemplate.objects.filter(case_types__id=case.type)


def get_letter_template_for_case(template_id, case):
    """
    Get the letter template via the ID but only if it can also be applied to the given case
    """
    try:
        return LetterTemplate.objects.get(pk=template_id, case_types__id=case.type)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": strings.Cases.LETTER_TEMPLATE_NOT_FOUND})


def get_generated_document_data(request_params, pk):
    template_id = request_params.get("template")
    if not template_id:
        raise AttributeError(strings.Cases.MISSING_TEMPLATE)

    text = request_params.get("text")
    if not text:
        raise AttributeError(strings.Cases.MISSING_TEXT)

    case = get_case(pk)
    template = get_letter_template_for_case(template_id, case)
    document_html = generate_preview(layout=template.layout.filename, text=markdown_to_html(text), case=case)

    if "error" in document_html:
        raise AttributeError(document_html["error"])

    return GeneratedDocumentPayload(case=case, template=template, document_html=document_html, text=text)


def get_generated_documents_for_exporter(case_pk, user, many=True):
    case = Case.objects.get(id=case_pk)
    if case.organisation != user.organisation:
        raise PermissionDeniedError(detail="You do not have access to that case")
    if many:
        documents = GeneratedCaseDocument.objects.filter(case=case)
        if user.type == UserType.EXPORTER:
            delete_exporter_notifications(
                user=user, organisation=user.organisation, objects=documents
            )
    else:
        documents = GeneratedCaseDocument.objects.get(case=case)
    return documents
