from itertools import permutations

from django.core.management import call_command
from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseType
from letter_templates.models import LetterTemplate
from picklists.enums import PickListStatus, PicklistType
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LetterTemplateCreateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        # Seed layouts
        call_command("seedlayouts")
        self.picklist_item_1 = self.create_picklist_item(
            "#1", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
        )
        self.picklist_item_2 = self.create_picklist_item(
            "#2", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
        )
        self.letter_layout = LetterLayout.objects.first()
        self.url = reverse("letter_templates:letter_templates")

    def test_create_letter_templates_success(self):
        """
        Successfully create a letter template
        """
        data = {
            "name": "Letter Template",
            "restricted_to": [CaseType.CLC_QUERY, CaseType.END_USER_ADVISORY_QUERY],
            "layout": self.letter_layout.id,
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        letter_template = LetterTemplate.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(letter_template.name, data["name"])
        self.assertEqual(letter_template.layout.id, data["layout"])
        self.assertIn(CaseType.CLC_QUERY, letter_template.restricted_to)
        self.assertIn(CaseType.END_USER_ADVISORY_QUERY, letter_template.restricted_to)

    def test_create_letter_templates_not_unique_name_failure(self):
        """
        Fail as the name is not unique
        """
        self.letter_template = LetterTemplate.objects.create(
            name="SIEL",
            restricted_to=[CaseType.CLC_QUERY, CaseType.END_USER_ADVISORY_QUERY],
            layout=self.letter_layout,
        )
        self.letter_template.letter_paragraphs.add(self.picklist_item_1)

        data = {
            "name": "SIEL",
            "restricted_to": [CaseType.CLC_QUERY],
            "layout": self.letter_layout.id,
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_letter_templates_no_letter_paragraphs_failure(self):
        """
        Fail as there are no letter paragraphs provided
        """
        data = {
            "name": "Letter Template",
            "restricted_to": [CaseType.CLC_QUERY],
            "layout": self.letter_layout.id,
            "letter_paragraphs": [],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_letter_templates_no_layout_failure(self):
        """
        Fail as a layout has not been provided
        """
        data = {
            "name": "Letter Template",
            "restricted_to": [CaseType.CLC_QUERY],
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_letter_templates_no_restricted_to_failure(self):
        """
        Fail as restricted to has not been provided
        """
        data = {
            "name": "Letter Template",
            "restricted_to": [],
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_letter_templates_order_is_saved(self):
        """Check the order of letter paragraphs is saved."""
        for i, picklist_items in enumerate(permutations([self.picklist_item_1, self.picklist_item_2])):
            name = f"Test Template {i}"
            data = {
                "name": name,
                "restricted_to": [CaseType.CLC_QUERY, CaseType.END_USER_ADVISORY_QUERY],
                "layout": self.letter_layout.id,
                "letter_paragraphs": [item.id for item in picklist_items],
            }
            response = self.client.post(self.url, data, **self.gov_headers)
            letter_template = LetterTemplate.objects.get(name=name)
            letter_paragraphs = letter_template.letter_paragraphs.all()
            self.assertEqual(letter_paragraphs[0].id, picklist_items[0].id)
            self.assertEqual(letter_paragraphs[1].id, picklist_items[1].id)
