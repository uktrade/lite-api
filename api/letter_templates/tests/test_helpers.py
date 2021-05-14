from bs4 import BeautifulSoup
from django.test import TestCase
from test_helpers.clients import DataTestClient
from api.letter_templates.helpers import generate_preview


class PreviewTestCase(TestCase):
    def test_generate_preview(self):
        generate_preview(layout="case_context_test", text="Hello World!")


class DocumentGenerationTestCase(DataTestClient):
    def test_document_layouts(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        layouts = [
            "application_form",
            "case_context_test",
            "ecju_queries_and_notes",
            "ecju",
            "nlr",
            "refusal",
            "siel",
        ]
        for layout in layouts:
            # check it renders with no errors
            assert generate_preview(layout=layout, case=case, text="")

    def test_siel_logo(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)

        html = generate_preview(layout="siel", case=case, text="")
        soup = BeautifulSoup(html, "html.parser")
        logo = soup.find(id="dit-logo")
        assert "data:image/png;base64" in logo["src"]
        assert len(logo["src"]) > 21
