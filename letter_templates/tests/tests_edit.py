from rest_framework import status
from rest_framework.reverse import reverse

from audit_trail.models import Audit
from audit_trail.payload import AuditType
from cases.enums import CaseTypeEnum
from conf import constants
from letter_templates.models import LetterTemplate
from picklists.enums import PickListStatus, PicklistType
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LetterTemplateEditTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user.role.permissions.set([constants.GovPermissions.CONFIGURE_TEMPLATES.name])

        self.picklist_item = self.create_picklist_item(
            "#1", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
        )
        self.letter_layout = LetterLayout.objects.first()
        self.letter_template = LetterTemplate.objects.create(name="SIEL", layout=self.letter_layout)
        self.letter_template.case_types.set([CaseTypeEnum.CLC_QUERY, CaseTypeEnum.END_USER_ADVISORY_QUERY])
        self.letter_template.letter_paragraphs.add(self.picklist_item)
        self.url = reverse("letter_templates:letter_template", kwargs={"pk": self.letter_template.id})

    def test_edit_letter_template_success(self):
        data = {"name": "Letter Template Edit"}

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], data["name"])

        audit_trail = Audit.objects.all()
        self.assertEqual(audit_trail.count(), 1)
        self.assertEqual(AuditType(audit_trail.first().verb), AuditType.UPDATED_LETTER_TEMPLATE_NAME)
