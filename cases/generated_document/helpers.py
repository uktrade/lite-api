from weasyprint import CSS, HTML

from conf.exceptions import NotFoundError
from letter_templates.helpers import get_css_location
from letter_templates.models import LetterTemplate
from lite_content.lite_api.letter_templates import LetterTemplatesPage


def html_to_pdf(html, template_name):
    html = HTML(string=html)
    css = CSS(filename=get_css_location(template_name))
    return html.write_pdf(stylesheets=[css])


def get_letter_template(id, case_type):
    """
    Returns a letter template or returns a 404 on failure
    """
    try:
        return LetterTemplate.objects.get(pk=id, restricted_to__contains=[case_type])
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": LetterTemplatesPage.NOT_FOUND_ERROR})
