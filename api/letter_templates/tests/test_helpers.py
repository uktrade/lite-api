from pathlib import Path

from django.test import modify_settings, TestCase

# import datetime
from django.test import TestCase

# from api.cases.tests.factories import CaseFactory
from api.letter_templates.context_generator import get_document_context
from test_helpers.clients import DataTestClient
from api.letter_templates.helpers import convert_var_to_text, generate_preview


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

    def test_convert_var_to_text(self):
        text = "Having carefully considered your application, {{ appeal_deadline }} {{ date_application_submitted }}"
        data = {"appeal_deadline": "22 August 2023", "date_application_submitted": "25 July 2023"}

        assert (
            convert_var_to_text(text, data)
            == "Having carefully considered your application, 22 August 2023 25 July 2023"
        )

    def test_get_document_context_without_base_application_name(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        base_application = case.baseapplication
        base_application.name = None
        base_application.save()

        data = get_document_context(case)
        assert data["exporter_reference"] == ""

    @modify_settings(INSTALLED_APPS={"append": "api.letter_templates.tests"})
    def test_markdown_and_variables(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        generated_preview = generate_preview(
            case=case,
            layout="user_content",
            text="""**{{ exporter_reference }}**
*{{ exporter_reference }}*
[{{ exporter_reference }}](http://example.com), {{ exporter_reference }}""",
        )
        with open(TEST_DATA_PATH / "markdown-variables.html") as expected_output_file:
            expected_output = expected_output_file.read()

        assert generated_preview == expected_output
