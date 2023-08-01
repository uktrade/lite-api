from pathlib import Path

from django.test import modify_settings, TestCase
from test_helpers.clients import DataTestClient
from api.letter_templates.helpers import generate_preview


TEST_DATA_PATH = Path(__file__).resolve().parent / "data"


@modify_settings(INSTALLED_APPS={"append": "api.letter_templates.tests"})
class PreviewTestCase(TestCase):
    def test_generate_preview(self):
        generated_preview = generate_preview(
            layout="case_context_test",
            text="Hello World!",
        )
        with open(TEST_DATA_PATH / "generated-preview.html") as expected_output_file:
            expected_output = expected_output_file.read()

        assert generated_preview == expected_output

    def test_markdown_formatting_generate_preview(self):
        generated_preview = generate_preview(
            layout="user_content",
            text="""**Strong**
*Emphasis*
[Link](http://example.com)""",
        )
        with open(TEST_DATA_PATH / "markdown-formatting.html") as expected_output_file:
            expected_output = expected_output_file.read()

        assert generated_preview == expected_output

    def test_escape_html_formatting_generate_preview(self):
        generated_preview = generate_preview(
            layout="user_content",
            text='<script>alert("This would be bad");</script>',
        )
        with open(TEST_DATA_PATH / "escape-html-formatting.html") as expected_output_file:
            expected_output = expected_output_file.read()

        assert generated_preview == expected_output

    def test_mixed_html_and_markdown_generate_preview(self):
        generated_preview = generate_preview(
            layout="user_content",
            text="""<script>alert("This would be bad");</script>
**But this is fine**""",
        )
        with open(TEST_DATA_PATH / "mixed-html-and-markdown-formatting.html") as expected_output_file:
            expected_output = expected_output_file.read()

        assert generated_preview == expected_output


class DocumentGenerationTestCase(DataTestClient):
    def test_document_layouts(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        layouts = [
            "application_form",
            "ecju_queries_and_notes",
            "ecju",
            "nlr",
            "refusal",
            "siel",
        ]
        for layout in layouts:
            # check it renders with no errors
            preview_output = generate_preview(layout=layout, case=case, text="")

        # Additional check to make sure that we actually get some output even if there are no errors
        assert preview_output
