from weasyprint import CSS, HTML

from letter_templates.helpers import get_css_location


def html_to_pdf(html, template_name):
    html = HTML(string=html)
    css = CSS(filename=get_css_location(template_name))
    return html.write_pdf(stylesheets=[css])
