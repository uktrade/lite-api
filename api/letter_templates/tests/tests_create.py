from itertools import permutations

from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseTypeEnum, CaseTypeReferenceEnum
from api.conf import constants
from api.letter_templates.models import LetterTemplate
from lite_content.lite_api import strings
from api.picklists.enums import PickListStatus, PicklistType
from api.staticdata.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LetterTemplateCreateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user.role.permissions.set([constants.GovPermissions.CONFIGURE_TEMPLATES.name])

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
            "case_types": [CaseTypeEnum.GOODS.reference, CaseTypeEnum.EUA.reference],
            "layout": self.letter_layout.id,
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
            "visible_to_exporter": "True",
            "include_digital_signature": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        letter_template = LetterTemplate.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(letter_template.name, data["name"])
        self.assertEqual(letter_template.visible_to_exporter, bool(data["visible_to_exporter"]))
        self.assertEqual(letter_template.layout.id, data["layout"])
        self.assertIn(
            CaseTypeEnum.GOODS.reference, letter_template.case_types.values_list("reference", flat=True),
        )
        self.assertIn(
            CaseTypeEnum.EUA.reference, letter_template.case_types.values_list("reference", flat=True),
        )

    def test_create_letter_templates_no_letter_paragraphs_success(self):
        data = {
            "name": "Letter Template",
            "case_types": [CaseTypeEnum.GOODS.reference],
            "layout": self.letter_layout.id,
            "letter_paragraphs": [],
            "visible_to_exporter": "True",
            "include_digital_signature": "False",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        letter_template = LetterTemplate.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(letter_template.name, data["name"])
        self.assertFalse(letter_template.letter_paragraphs.exists())

    def test_create_letter_templates_not_unique_name_failure(self):
        """
        Fail as the name is not unique
        """
        self.letter_template = self.create_letter_template(
            name="SIEL", case_types=[CaseTypeEnum.GOODS.id, CaseTypeEnum.EUA.id], letter_paragraph=self.picklist_item_1
        )

        data = {
            "name": "SIEL",
            "case_types": [CaseTypeEnum.GOODS.reference],
            "layout": self.letter_layout.id,
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
            "visible_to_exporter": "True",
            "include_digital_signature": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"name": [strings.LetterTemplates.UNIQUE_NAME]})

    def test_create_letter_templates_no_layout_failure(self):
        """
        Fail as a layout has not been provided
        """
        data = {
            "name": "Letter Template",
            "case_types": [CaseTypeEnum.GOODS.reference],
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
            "visible_to_exporter": "True",
            "include_digital_signature": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"layout": [strings.LetterTemplates.SELECT_THE_LAYOUT]})

    def test_create_letter_templates_no_case_types_failure(self):
        """
        Fail as restricted to has not been provided
        """
        data = {
            "name": "Letter Template",
            "case_types": [],
            "layout": self.letter_layout.id,
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
            "visible_to_exporter": "True",
            "include_digital_signature": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"], {"case_types": [strings.LetterTemplates.NEED_AT_LEAST_ONE_CASE_TYPE]}
        )

    def test_create_letter_templates_no_visible_to_exporter_failure(self):
        data = {
            "name": "Letter Template",
            "case_types": [CaseTypeEnum.GOODS.reference],
            "layout": self.letter_layout.id,
            "letter_paragraphs": [],
            "include_digital_signature": "False",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"], {"visible_to_exporter": [strings.LetterTemplates.VISIBLE_TO_EXPORTER]}
        )

    def test_create_letter_templates_no_include_digital_signature_failure(self):
        data = {
            "name": "Letter Template",
            "case_types": [CaseTypeEnum.GOODS.reference],
            "layout": self.letter_layout.id,
            "letter_paragraphs": [],
            "visible_to_exporter": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            {"include_digital_signature": [strings.LetterTemplates.INCLUDE_DIGITAL_SIGNATURE]},
        )

    def test_create_letter_templates_order_is_saved(self):
        """Check the order of letter paragraphs is saved."""
        for i, picklist_items in enumerate(permutations([self.picklist_item_1, self.picklist_item_2])):
            name = f"Test Template {i}"
            data = {
                "name": name,
                "case_types": [CaseTypeEnum.GOODS.reference, CaseTypeEnum.EUA.reference],
                "layout": self.letter_layout.id,
                "letter_paragraphs": [item.id for item in picklist_items],
                "visible_to_exporter": "True",
                "include_digital_signature": "False",
            }
            self.client.post(self.url, data, **self.gov_headers)
            letter_template = LetterTemplate.objects.get(name=name)
            letter_paragraphs = letter_template.letter_paragraphs.all()
            self.assertEqual(letter_paragraphs[0].id, picklist_items[0].id)
            self.assertEqual(letter_paragraphs[1].id, picklist_items[1].id)

    def test_create_letter_template_with_decisions_success(self):
        case_type_references = [CaseTypeEnum.SIEL.reference, CaseTypeEnum.OIEL.reference]
        data = {
            "name": "Letter Template",
            "case_types": case_type_references,
            "layout": self.letter_layout.id,
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
            "decisions": ["proviso", "approve"],
            "visible_to_exporter": "True",
            "include_digital_signature": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_decisions = response.json()["decisions"]
        self.assertEqual(len(response_decisions), len(data["decisions"]))
        for decision in data["decisions"]:
            self.assertIn(decision, [response_decision["name"]["key"] for response_decision in response_decisions])

    def test_create_letter_template_with_decisions_on_non_application_case_types_failure(self):
        case_type_references = [CaseTypeEnum.EUA.reference, CaseTypeEnum.GOODS.reference]
        case_type_reference_values = [CaseTypeReferenceEnum.get_text(reference) for reference in case_type_references]
        data = {
            "name": "Letter Template",
            "case_types": case_type_references,
            "layout": self.letter_layout.id,
            "letter_paragraphs": [self.picklist_item_1.id, self.picklist_item_2.id],
            "decisions": ["proviso", "approve"],
            "visible_to_exporter": "True",
            "include_digital_signature": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["case_types"],
            [
                strings.LetterTemplates.DECISIONS_NON_APPLICATION_CASE_TYPES_ERROR
                + ", ".join(case_type_reference_values)
            ],
        )
