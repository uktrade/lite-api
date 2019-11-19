from weasyprint import CSS, HTML

from conf.settings import BASE_DIR

CSS_LOCATION = '/assets/css/styles.css'


def html_to_pdf(html):
    html = HTML(string=html)
    css = CSS(filename=BASE_DIR+CSS_LOCATION)
    return html.write_pdf(stylesheets=[css])
