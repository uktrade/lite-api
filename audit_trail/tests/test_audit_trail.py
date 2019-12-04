from test_helpers.clients import DataTestClient


class CasesAuditTrail(DataTestClient):
    # TODO: test schema and creation
    def setUp(self):
        super().setUp()
        self.draft = self.create_open_application(self.organisation)

    def test_cases_audit_trail(self):
        assert 1
