from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseType
from letter_templates.models import LetterTemplate
from picklists.enums import PickListStatus, PicklistType
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LetterTemplateEditTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item(
            "#1", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
        )
        self.letter_layout = LetterLayout.objects.first()
        self.letter_template = LetterTemplate.objects.create(
            name="SIEL",
            restricted_to=[CaseType.CLC_QUERY, CaseType.END_USER_ADVISORY_QUERY],
            layout=self.letter_layout,
        )
        self.letter_template.letter_paragraphs.add(self.picklist_item)
        self.url = reverse("letter_templates:letter_template", kwargs={"pk": self.letter_template.id})

    def test_edit_letter_template(self):
        data = {"name": "Letter Template Edit"}

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], data["name"])
