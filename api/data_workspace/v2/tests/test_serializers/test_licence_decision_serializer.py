import datetime

from django.test import TestCase
from parameterized import parameterized

from api.audit_trail.enums import AuditType
from api.audit_trail.tests.factories import AuditFactory
from api.applications.tests.factories import StandardApplicationFactory
from api.data_workspace.v2.serializers import LicenceDecisionSerializer
from api.licences.enums import LicenceDecisionType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class LicenceDecisionSerializerTests(TestCase):

    @parameterized.expand(["withdrawn", "Withdrawn"])
    def test_decision_made_at_with_withdrawn_status(self, status_name):
        application = StandardApplicationFactory(status=get_case_status_by_status(CaseStatusEnum.WITHDRAWN))
        audit = AuditFactory(
            payload={"status": {"new": status_name}},
            target=application.get_case(),
            verb=AuditType.UPDATED_STATUS,
        )
        serializer = LicenceDecisionSerializer(instance=application)
        assert serializer.data["decision_made_at"] == audit.created_at

    def test_finalised_and_issued_without_sub_status_with_granted_application_audit(self):
        application = StandardApplicationFactory(status=get_case_status_by_status(CaseStatusEnum.FINALISED))
        assert application.sub_status is None
        audit = AuditFactory(
            payload={
                "start_date": datetime.date.today().isoformat(),
                "licence_duration": "12",
            },
            target=application.get_case(),
            verb=AuditType.GRANTED_APPLICATION,
        )
        serializer = LicenceDecisionSerializer(instance=application)
        assert serializer.data["decision"] == LicenceDecisionType.ISSUED
        assert serializer.data["decision_made_at"] == audit.created_at

    def test_finalised_and_refused_without_sub_status_with_refusal_letter_generated_audit(self):
        application = StandardApplicationFactory(status=get_case_status_by_status(CaseStatusEnum.FINALISED))
        assert application.sub_status is None
        audit = AuditFactory(
            payload={
                "file_name": "madeupfile.doc",
                "template": "Refusal letter template",
            },
            target=application.get_case(),
            verb=AuditType.GENERATE_CASE_DOCUMENT,
        )
        serializer = LicenceDecisionSerializer(instance=application)
        assert serializer.data["decision"] == LicenceDecisionType.REFUSED
        assert serializer.data["decision_made_at"] == audit.created_at

    def test_finalised_and_nlr_without_sub_status_with_nlr_letter_generated_audit(self):
        application = StandardApplicationFactory(status=get_case_status_by_status(CaseStatusEnum.FINALISED))
        assert application.sub_status is None
        audit = AuditFactory(
            payload={
                "file_name": "madeupfile.doc",
                "template": "No licence required letter template",
            },
            target=application.get_case(),
            verb=AuditType.GENERATE_CASE_DOCUMENT,
        )
        serializer = LicenceDecisionSerializer(instance=application)
        assert serializer.data["decision"] == LicenceDecisionType.NLR
        assert serializer.data["decision_made_at"] == audit.created_at
