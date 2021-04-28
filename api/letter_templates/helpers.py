import bleach
import os

from django.template import Context, Engine, TemplateDoesNotExist
from django.utils.html import mark_safe
from markdown import markdown

from django.conf import settings
from api.core.exceptions import NotFoundError
from api.conf.settings import CSS_ROOT
from api.letter_templates.context_generator import get_document_context
from api.letter_templates.exceptions import InvalidVarException
from api.letter_templates.models import LetterTemplate
from lite_content.lite_api import strings


ALLOWED_TAGS = ["b", "strong", "em", "u", "h1", "h2", "h3", "h4", "h5", "h6"]


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
        builtins=[
            "django.template.defaulttags",
            "django.template.defaultfilters",
            "django.template.loader_tags",
            "api.letter_templates.templatetags.custom_tags",
        ],
        dirs=[os.path.join(settings.LETTER_TEMPLATES_DIRECTORY)],
        libraries={
            "static": "django.templatetags.static",
            "custom_tags": "api.letter_templates.templatetags.custom_tags",
        },
    )


def markdown_to_html(text: str):
    return markdown(text, extensions=["nl2br"])


def get_paragraphs_as_html(paragraphs: list):
    return "\n\n".join([paragraph.text for paragraph in paragraphs])


def get_css_location(filename):
    return os.path.join(CSS_ROOT, filename + ".css")


def load_css(filename):
    with open(get_css_location(filename)) as css_file:
        css = css_file.read()
    return f"<style>\n{css}</style>\n"


def format_user_text(user_text):
    cleaned_text = bleach.clean(user_text, tags=ALLOWED_TAGS)
    return markdown_to_html(mark_safe(cleaned_text))


class DocumentPreviewError(Exception):
    pass


def generate_preview(
    layout: str,
    text: str,
    case=None,
    additional_contact=None,
    allow_missing_variables=True,
    include_digital_signature=False,
):
    try:
        django_engine = template_engine_factory(allow_missing_variables)
        template = django_engine.get_template(f"{layout}.html")

        context = {"include_digital_signature": include_digital_signature, "user_content": text}
        if case:
            context = {**context, **get_document_context(case, additional_contact)}

        return load_css(layout) + template.render(Context(context))
    except (FileNotFoundError, TemplateDoesNotExist):
        raise DocumentPreviewError(strings.LetterTemplates.PREVIEW_ERROR)
