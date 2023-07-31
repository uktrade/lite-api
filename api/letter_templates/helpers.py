import bleach
import os

from django.template.loader import render_to_string
from django.utils.html import (
    escape,
    mark_safe,
)
from markdown import markdown

from api.conf.settings import CSS_ROOT
from api.letter_templates.context_generator import get_document_context


ALLOWED_TAGS = ["b", "strong", "em", "u", "h1", "h2", "h3", "h4", "h5", "h6"]


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


def convert_user_content(text):
    text = escape(text)
    text = markdown_to_html(text)
    text = mark_safe(text)

    return text


def generate_preview(
    layout: str,
    text: str,
    case=None,
    additional_contact=None,
    include_digital_signature=False,
    include_css=True,
):
    template_name = f"letter_templates/{layout}.html"

    css_string = ""
    if include_css:
        css_string = load_css(layout)
        if layout == "siel":
            css_string = load_css("siel_preview")

    context = {
        "include_digital_signature": include_digital_signature,
        "user_content": convert_user_content(text),
        "css": css_string,
    }
    if case:
        context.update(get_document_context(case, additional_contact))

    return render_to_string(template_name, context)
