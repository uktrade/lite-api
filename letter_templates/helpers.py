import os

from django.template import Context, Engine, TemplateDoesNotExist
from markdown import Markdown

from conf import settings
from conf.exceptions import NotFoundError
from conf.settings import BASE_DIR
from letter_templates.models import LetterTemplate


CSS_LOCATION = "assets/css/"


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
        dirs=[os.path.join(settings.LETTER_TEMPLATES_DIRECTORY)]
    )


def get_paragraphs_as_html(paragraphs: list):
    return "\n\n".join([Markdown().convert(paragraph.text) for paragraph in paragraphs])


def get_css_location(filename):
    return BASE_DIR + "/" + CSS_LOCATION + filename + ".css"


def load_css(filename):
    with open(get_css_location(filename)) as css_file:
        css = css_file.read()
    return "<style>\n"+css+"</style>\n"


def generate_preview(layout: str, paragraphs: list, case=None, allow_missing_variables=True):
    try:
        django_engine = template_engine_factory(allow_missing_variables)
        css = load_css(layout)
        template = django_engine.get_template(f"{layout}.html")

        context = {"content": get_paragraphs_as_html(paragraphs)}
        template = template.render(Context(context))
        if case:
            context = {"case": case}
            template = django_engine.from_string(template)
            template = template.render(Context(context))

        return css + template
    except (FileNotFoundError, TemplateDoesNotExist):
        return {"error": "Document preview is not available at this time"}


def get_preview(template: LetterTemplate, case=None):
    paragraphs = template.letter_paragraphs.all()
    return generate_preview(template.layout.filename, paragraphs=paragraphs, case=case)
