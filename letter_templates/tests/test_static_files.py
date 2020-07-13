import os

from conf.settings import LETTER_TEMPLATES_DIRECTORY, CSS_ROOT
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LayoutStaticFileTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.layouts = LetterLayout.objects.values_list("filename", flat=True)

    def test_html_files_are_present(self):
        html_files_in_directory = set(os.listdir(LETTER_TEMPLATES_DIRECTORY))
        html_files_required = set([f"{layout}.html" for layout in self.layouts])

        self.assertTrue(
            html_files_required.issubset(html_files_in_directory),
            msg=f"Missing layouts: {html_files_required.difference(html_files_in_directory)}",
        )

    def test_css_files_are_present(self):
        css_files_in_directory = set(os.listdir(CSS_ROOT))
        css_files_required = set([f"{layout}.css" for layout in self.layouts])

        self.assertTrue(
            css_files_required.issubset(css_files_in_directory),
            msg=f"Missing css sheets: {css_files_required.difference(css_files_in_directory)}",
        )
