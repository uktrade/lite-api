from weasyprint import CSS, HTML

from conf.exceptions import NotFoundError
from letter_templates.helpers import get_css_location
from letter_templates.models import LetterTemplate, TemplateCaseTypes
from lite_content.lite_internal_frontend.letter_templates import LetterTemplatesPage


def html_to_pdf(html, template_name):
    html = HTML(string=html)
    css = CSS(filename=get_css_location(template_name.split(" ")[0].lower()))
    return html.write_pdf(stylesheets=[css])


def get_letter_templates_for_case(case):
    try:
        return TemplateCaseTypes.objects.filter(case_type=case.type).values_list("letter_template")
    except TemplateCaseTypes.DoesNotExist:
        raise NotFoundError({"letter_template": LetterTemplatesPage.NOT_FOUND_ERROR})


def get_letter_template_for_case(id, case):
    try:
        return TemplateCaseTypes.objects.get(letter_template__pk=id, case_type=case.type).letter_template
    except TemplateCaseTypes.DoesNotExist:
        raise NotFoundError({"letter_template": LetterTemplatesPage.NOT_FOUND_ERROR})


def get_letter_template(id):
    """
    Returns a letter template or returns a 404 on failure
    """
    try:
        return LetterTemplate.objects.get(pk=id)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": LetterTemplatesPage.NOT_FOUND_ERROR})
