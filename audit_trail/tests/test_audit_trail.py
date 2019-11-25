from test_helpers.clients import DataTestClient
from actstream.models import Action


class CasesAuditTrail(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_open_application(self.organisation)

    def test_cases_audit_trail(self):
        assert 0
