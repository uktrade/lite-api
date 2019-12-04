import os

from django.template import Context, Engine, TemplateDoesNotExist
from markdown import markdown

from conf import settings
from conf.exceptions import NotFoundError
from conf.settings import CSS_ROOT
from letter_templates.exceptions import InvalidVarException
from letter_templates.models import LetterTemplate
from lite_content.lite_api.letter_templates import LetterTemplatesPage


def get_letter_template(pk):
    try:
        return LetterTemplate.objects.get(pk=pk)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": "LetterTemplate not found - " + str(pk)})


def template_engine_factory(allow_missing_variables):
    """
    Create a template engine configured for use with letter templates.
    """
    # Put the variable name in if missing variables. Else trigger an InvalidVarException.
    string_if_invalid = "{{ %s }}" if allow_missing_variables else InvalidVarException()

    return Engine(
        string_if_invalid=string_if_invalid,
        dirs=[os.path.join(settings.LETTER_TEMPLATES_DIRECTORY)],
        libraries={"static": "django.templatetags.static"},
    )


def markdown_to_html(text: str):
    return markdown(text, extensions=["nl2br"])


def get_paragraphs_as_html(paragraphs: list):
    return "\n\n".join([markdown_to_html(paragraph.text)for paragraph in paragraphs])


def get_css_location(filename):
    return os.path.join(CSS_ROOT, filename + ".css")


def load_css(filename):
    with open(get_css_location(filename)) as css_file:
        css = css_file.read()
    return f"<style>\n{css}</style>\n"


def generate_preview(layout: str, text: str, case=None, allow_missing_variables=True):
    try:
        django_engine = template_engine_factory(allow_missing_variables)
        template = django_engine.get_template(f"{layout}.html")

        context = {"content": text}
        template = template.render(Context(context))
        if case:
            context = {"case": case}
            template = django_engine.from_string(template)
            template = template.render(Context(context))

        return load_css(layout) + template
    except (FileNotFoundError, TemplateDoesNotExist):
        return {"error": LetterTemplatesPage.PREVIEW_ERROR}


def get_preview(template: LetterTemplate, text: str, case=None):
    return generate_preview(template.layout.filename, text=text, case=case)
