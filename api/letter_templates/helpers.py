import os
from django.template import Context, Template

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import (
    escape,
    mark_safe,
)
from markdown import markdown

from api.letter_templates.context_generator import get_document_context


class DocumentPreviewError(Exception):
    pass


def markdown_to_html(text: str):
    return markdown(text, extensions=["nl2br"])


def get_paragraphs_as_html(paragraphs: list):
    return "\n\n".join([paragraph.text for paragraph in paragraphs])


def get_css_location(filename):
    return os.path.join(settings.CSS_ROOT, filename + ".css")


def load_css(filename):
    with open(get_css_location(filename)) as css_file:
        css = css_file.read()
    return f"<style>\n{css}</style>\n"


def format_user_text(text):
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
        "user_content": format_user_text(text),
        "css": css_string,
    }

    if case:
        context.update(get_document_context(case, additional_contact))
        context["user_content"] = format_user_text(convert_var_to_text(text, context))

    return render_to_string(template_name, context)


def convert_var_to_text(text, data):
    template = Template(text)
    context = Context(data)

    return template.render(context)
