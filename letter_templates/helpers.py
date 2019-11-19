import os

from django.template import Context, Engine
from weasyprint import HTML, CSS

from conf import settings
from conf.exceptions import NotFoundError
from conf.settings import BASE_DIR
from letter_templates.models import LetterTemplate

CSS_LOCATION = '/assets/css/styles.css'


def get_letter_template(pk):
    try:
        return LetterTemplate.objects.get(pk=pk)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": "LetterTemplate not found - " + str(pk)})


class InvalidVarException(Exception):
    """
    InvalidVarException is triggered by the django template engine when it cannot
    find a context variable. This exception should be handled in places where the
    template may use an invalid variable (user entered variables)
    """

    def __mod__(self, missing):
        raise InvalidVarException("Invalid template variable {{ %s }}" % missing)

    def __contains__(self, search):
        if search == "%s":
            return True
        return False


def template_engine_factory(allow_missing_variables):
    """
    Create a template engine configured for use with letter templates.
    """
    # Put the variable name in if missing variables. Else trigger an InvalidVarException.
    string_if_invalid = "{{ %s }}" if allow_missing_variables else InvalidVarException()
    return Engine(
        string_if_invalid=string_if_invalid,
        dirs=[os.path.join(settings.LETTER_TEMPLATES_DIRECTORY)],
        libraries={"sass_tags": "sass_processor.templatetags.sass_tags"},
    )


def markdown_to_html(text):
    return Markdown().convert(text)


def html_to_pdf(html):
    html = HTML(string=html)
    css = CSS(filename=BASE_DIR+CSS_LOCATION)
    return html.write_pdf(stylesheets=[css])


def generate_preview(layout, content: dict, allow_missing_variables=True):
    django_engine = template_engine_factory(allow_missing_variables)
    template = django_engine.get_template(f"{layout}.html")
    return template.render(Context(content))

