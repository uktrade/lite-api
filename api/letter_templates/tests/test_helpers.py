from pathlib import Path

from django.test import modify_settings, TestCase
import datetime
from django.test import TestCase
from test_helpers.clients import DataTestClient
from api.letter_templates.helpers import convert_var_to_text, generate_preview, get_additional_var_data_for_template


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

    def test_document_variables(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)

        generate_preview(
            layout="refusal",
            case=case,
            text="Having carefully considered your application, {{ appeal_deadline }} {{ date_application_submitted }}",
        )

    def test_get_additional_var_data_for_template(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)

        today = datetime.date.today()
        case.baseapplication.submitted_at = today

        appeal_deadline = today + datetime.timedelta(days=28)
        date_application_submitted = case.baseapplication.submitted_at
        exporter_reference = case.baseapplication.name

        data = get_additional_var_data_for_template(case)

        assert data["appeal_deadline"] == appeal_deadline.strftime("%d %B %Y")
        assert data["date_application_submitted"] == date_application_submitted.strftime("%d %B %Y")
        assert data["exporter_reference"] == exporter_reference
        assert len(data) == 3

    def test_convert_var_to_text(self):
        text = "Having carefully considered your application, {{ appeal_deadline }} {{ date_application_submitted }}"
        data = {"appeal_deadline": "22 August 2023", "date_application_submitted": "25 July 2023"}

        assert (
            convert_var_to_text(text, data)
            == "Having carefully considered your application, 22 August 2023 25 July 2023"
        )
