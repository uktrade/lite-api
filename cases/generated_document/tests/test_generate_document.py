from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseType
from letter_templates.models import LetterTemplate
from picklists.enums import PickListStatus, PicklistType
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class GenerateDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item(
            "#1", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
        )
        self.letter_layout = LetterLayout.objects.first()
        self.letter_template = LetterTemplate.objects.create(
            name="SIEL", restricted_to=[CaseType.APPLICATION], layout=self.letter_layout,
        )
        self.letter_template.letter_paragraphs.add(self.picklist_item)
        self.case = self.create_standard_application_case(self.organisation)
        self.data = {"template": str(self.letter_template.id)}
        self.url = reverse("generated_documents:generated_documents", kwargs={"pk": str(self.case.pk)})

    def test_generate_document_success(self):
        response = self.client.post(self.url, **self.gov_headers, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
