from uuid import UUID
from _pytest.monkeypatch import MonkeyPatch
from parameterized import parameterized
import uuid
from unittest import mock
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.cases.enums import AdviceType

from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient
from api.cases.generated_documents.tests.factories import GeneratedCaseDocumentFactory
from api.cases.generated_documents import views
from api.letter_templates.models import LetterTemplate
from api.staticdata.statuses.models import CaseStatus, CaseSubStatus
from api.staticdata.statuses.enums import CaseSubStatusIdEnum


class GeneratedDocumentSendTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)

    def test_post_generated_document_missing(self):

        url = reverse(
            "cases:generated_documents:send_generated_document",
            kwargs={"document_pk": uuid.uuid4(), "pk": self.case.id},
        )
        response = self.client.post(url, **self.gov_headers)
        assert response.status_code == 404

    def test_post_no_notification(self):

        generated_document = GeneratedCaseDocumentFactory(
            template=LetterTemplate.objects.first(),
            case=self.case,
            visible_to_exporter=False,
            advice_type=AdviceType.INFORM,
        )

        url = reverse(
            "cases:generated_documents:send_generated_document",
            kwargs={"document_pk": generated_document.id, "pk": self.case.id},
        )
        response = self.client.post(url, **self.gov_headers)
        assert response.status_code == 200
        assert response.json() == {
            "notification_sent": False,
            "document": {
                "advice_type": generated_document.advice_type,
                "template": str(generated_document.template.id),
                "text": generated_document.text,
            },
        }
        generated_document.refresh_from_db()
        assert generated_document.visible_to_exporter == True
        # Check add audit
        self.assertEqual(Audit.objects.all().count(), 2)

        audit = Audit.objects.all().first()
        self.assertEqual(AuditType(audit.verb), AuditType.DECISION_LETTER_SENT)
        self.assertEqual(
            audit.payload,
            {"decision": "inform", "case_reference": "GBSIEL/2023/0000001/P"},
        )
        audit_text = AuditSerializer(audit).data["text"]
        self.assertEqual(audit_text, "sent an inform letter.")
        assert self.case.sub_status == None

    @parameterized.expand(
        [
            ("under_final_review", UUID(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT)),
            ("ogd_advice", None),
        ]
    )
    def test_post_with_notification(self, case_status, expected_sub_status_id):
        self.case.status = CaseStatus.objects.get(status=case_status)
        self.case.save()
        mocked_notify_function = mock.Mock()
        MonkeyPatch().setitem(views.NOTIFICATION_FUNCTIONS, "inform_letter", mocked_notify_function)

        generated_document = GeneratedCaseDocumentFactory(
            template=LetterTemplate.objects.first(),
            case=self.case,
            visible_to_exporter=False,
            advice_type=AdviceType.INFORM,
        )
        generated_document.template.layout.filename = "inform_letter"
        generated_document.template.layout.save()

        url = reverse(
            "cases:generated_documents:send_generated_document",
            kwargs={"document_pk": generated_document.id, "pk": self.case.id},
        )
        response = self.client.post(url, **self.gov_headers)
        assert response.status_code == 200
        assert response.json() == {
            "notification_sent": True,
            "document": {
                "advice_type": generated_document.advice_type,
                "template": str(generated_document.template.id),
                "text": generated_document.text,
            },
        }
        generated_document.refresh_from_db()
        assert generated_document.visible_to_exporter == True
        mocked_notify_function.assert_called_with(self.case.get_case())

        # Check add audit
        self.assertEqual(Audit.objects.all().count(), 2)
        audit = Audit.objects.all().first()
        self.assertEqual(AuditType(audit.verb), AuditType.DECISION_LETTER_SENT)
        self.assertEqual(
            audit.payload,
            {"decision": "inform", "case_reference": "GBSIEL/2023/0000001/P"},
        )

        audit_text = AuditSerializer(audit).data["text"]
        self.assertEqual(audit_text, "sent an inform letter.")
        self.case.refresh_from_db()
        assert self.case.sub_status_id == expected_sub_status_id
