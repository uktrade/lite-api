from django.test import TestCase
from parameterized import parameterized

from api.audit_trail.enums import AuditType
from api.audit_trail.tests.factories import AuditFactory
from api.applications.tests.factories import StandardApplicationFactory
from api.data_workspace.v2.serializers import LicenceDecisionSerializer
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
