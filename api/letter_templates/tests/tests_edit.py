from rest_framework import status
from rest_framework.reverse import reverse

from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from cases.enums import CaseTypeEnum, CaseTypeReferenceEnum, AdviceType
from api.conf import constants
from lite_content.lite_api import strings
from api.picklists.enums import PicklistType, PickListStatus
from api.static.decisions.models import Decision
from test_helpers.clients import DataTestClient


class LetterTemplateEditTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user.role.permissions.set([constants.GovPermissions.CONFIGURE_TEMPLATES.name])
        self.letter_template = self.create_letter_template(
            name="SIEL",
            case_types=[CaseTypeEnum.SIEL.id, CaseTypeEnum.OIEL.id],
            decisions=[Decision.objects.get(name="refuse"), Decision.objects.get(name="no_licence_required")],
        )
        self.url = reverse("letter_templates:letter_template", kwargs={"pk": self.letter_template.id})

    def test_edit_letter_template_name_success(self):
        data = {"name": "Letter Template Edit"}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], data["name"])
        self.assertEqual(Audit.objects.filter(verb=AuditType.UPDATED_LETTER_TEMPLATE_NAME).count(), 1)

    def test_edit_letter_template_case_types_success(self):
        data = {"case_types": [CaseTypeReferenceEnum.OICL, CaseTypeReferenceEnum.SIEL]}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_case_types = response.json()["case_types"]
        self.assertEqual(len(response_case_types), len(data["case_types"]))
        for case_type in data["case_types"]:
            self.assertIn(
                case_type, [response_case_type["reference"]["key"] for response_case_type in response_case_types]
            )
        self.assertEqual(Audit.objects.filter(verb=AuditType.UPDATED_LETTER_TEMPLATE_CASE_TYPES).count(), 1)

    def test_edit_letter_template_decisions_success(self):
        data = {"decisions": [AdviceType.PROVISO, AdviceType.APPROVE]}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_decisions = response.json()["decisions"]
        self.assertEqual(len(response_decisions), len(data["decisions"]))
        for decision in data["decisions"]:
            self.assertIn(decision, [response_decision["name"]["key"] for response_decision in response_decisions])
        self.assertEqual(Audit.objects.filter(verb=AuditType.UPDATED_LETTER_TEMPLATE_DECISIONS).count(), 1)

    def test_edit_letter_template_decisions_on_non_application_case_types_failure(self):
        case_type_ids = [CaseTypeEnum.GOODS.id, CaseTypeEnum.EUA.id]
        case_type_references = [
            CaseTypeReferenceEnum.get_text(reference)
            for reference in [CaseTypeEnum.EUA.reference, CaseTypeEnum.GOODS.reference]
        ]
        self.letter_template.case_types.set(case_type_ids)
        data = {"decisions": ["proviso", "approve"]}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["case_types"],
            [strings.LetterTemplates.DECISIONS_NON_APPLICATION_CASE_TYPES_ERROR + ", ".join(case_type_references)],
        )
        self.assertEqual(Audit.objects.count(), 0)

    def test_edit_letter_template_edit_paragraphs_success(self):
        letter_paragraph = self.create_picklist_item(
            "#2", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
        )
        data = {"letter_paragraphs": [str(letter_paragraph.pk)]}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["letter_paragraphs"], [str(letter_paragraph.pk)])
        self.assertEqual(Audit.objects.filter(verb=AuditType.UPDATED_LETTER_TEMPLATE_PARAGRAPHS).count(), 1)

    def test_edit_letter_template_remove_last_paragraph_success(self):
        data = {"letter_paragraphs": []}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["letter_paragraphs"], [])
        self.assertEqual(Audit.objects.filter(verb=AuditType.REMOVED_LETTER_TEMPLATE_PARAGRAPHS).count(), 1)

    def test_edit_letter_template_add_first_paragraph_success(self):
        self.letter_template.letter_paragraphs.set([])
        letter_paragraph = self.create_picklist_item(
            "#2", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
        )
        data = {"letter_paragraphs": [str(letter_paragraph.pk)]}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["letter_paragraphs"], [str(letter_paragraph.pk)])
        self.assertEqual(Audit.objects.filter(verb=AuditType.ADDED_LETTER_TEMPLATE_PARAGRAPHS).count(), 1)
