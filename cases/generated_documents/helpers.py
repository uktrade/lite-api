from weasyprint import CSS, HTML
from weasyprint.fonts import FontConfiguration

from conf.exceptions import NotFoundError
from letter_templates.helpers import get_css_location
from letter_templates.models import LetterTemplate
from lite_content.lite_api.letter_templates import LetterTemplatesPage

FONT_CONFIG = FontConfiguration()


def html_to_pdf(request, html: str, template_name: str):
    html = HTML(string=html, base_url=request.build_absolute_uri())
    css = CSS(filename=get_css_location(template_name), font_config=FONT_CONFIG)
    return html.write_pdf(stylesheets=[css], font_config=FONT_CONFIG)


def get_letter_templates_for_case(case):
    return LetterTemplate.objects.filter(case_types__id=case.type)


def get_letter_template_for_case(id, case):
    """
    Get the letter template via the ID but only if it can also be applied to the given case
    """
    try:
        return LetterTemplate.objects.get(pk=id, case_types__id=case.type)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": LetterTemplatesPage.NOT_FOUND_ERROR})


def get_letter_template(id):
    """
    Returns a letter template or returns a 404 on failure
    """
    try:
        return LetterTemplate.objects.get(pk=id)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": LetterTemplatesPage.NOT_FOUND_ERROR})
