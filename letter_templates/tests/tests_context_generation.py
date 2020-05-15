from cases.enums import AdviceLevel, AdviceType
from letter_templates.context_generator import get_document_context
from test_helpers.clients import DataTestClient


class DocumentContextGenerationTests(DataTestClient):
    def test_generate_context(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        final_advice = self.create_advice(
            self.gov_user, case, "good", AdviceType.APPROVE, AdviceLevel.FINAL, advice_text="abc",
        )

        result = get_document_context(case)
