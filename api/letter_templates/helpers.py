import bleach
import os

from django.template.loader import render_to_string
from django.utils.html import mark_safe
from markdown import markdown

from api.core.exceptions import NotFoundError
from api.conf.settings import CSS_ROOT
from api.letter_templates.context_generator import get_document_context
from api.letter_templates.models import LetterTemplate
from api.letter_templates.constants import TemplateTitles
import jinja2

ALLOWED_TAGS = ["b", "strong", "em", "u", "h1", "h2", "h3", "h4", "h5", "h6"]


def get_letter_template(pk):
    try:
        return LetterTemplate.objects.get(pk=pk)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError({"letter_template": "LetterTemplate not found - " + str(pk)})


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
    include_digital_signature=False,
    include_css=True,
):
    template_name = f"letter_templates/{layout}.html"
    title = ""

    if layout == "nlr":
        title = TemplateTitles.NLR
    if layout == "refusal":
        title = TemplateTitles.REFUSAL_LETTER
    if layout == "application_form":
        title = TemplateTitles.APPLICATION_FORM
    if layout == "siel":
        title = TemplateTitles.SIEL

    context = {"include_digital_signature": include_digital_signature, "user_content": text, "title": title}
    if case:
        context = {**context, **get_document_context(case, additional_contact)}

    context["user_content"] = recursive_render(text, context)

    css_string = ""
    if include_css:
        css_string = load_css(layout)
        if layout == "siel":
            css_string = load_css("siel_preview")
    context["css"] = css_string
    return render_to_string(template_name, context)


def recursive_render(tpl, values):
    prev = tpl
    while True:
        curr = jinja2.Template(prev).render(**values)
        if curr != prev:
            prev = curr
        else:
            return curr
