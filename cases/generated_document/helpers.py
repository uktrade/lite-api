from os import path
from weasyprint import CSS, HTML
from conf.settings import BASE_DIR

CSS_LOCATION = "assets/css/styles.scss"


def html_to_pdf(html):
    html = HTML(string=html)
    css = CSS(filename=path.join(BASE_DIR, CSS_LOCATION))
    return html.write_pdf(stylesheets=[css])
