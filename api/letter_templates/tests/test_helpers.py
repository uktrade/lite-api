from pathlib import Path

from django.test import modify_settings, TestCase

from test_helpers.clients import DataTestClient
from api.letter_templates.helpers import generate_preview


TEST_DATA_PATH = Path(__file__).resolve().parent / "data"


class PreviewTestCase(TestCase):
    @modify_settings(INSTALLED_APPS={"append": "api.letter_templates.tests"})
    def test_generate_preview(self):
        generated_preview = generate_preview(
            layout="case_context_test",
            text="Hello World!",
        )
        with open(TEST_DATA_PATH / "generated-preview.html") as expected_output_file:
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
