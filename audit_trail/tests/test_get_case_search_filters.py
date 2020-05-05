from audit_trail.service import get_case_activity_filters

from audit_trail.tests.factories import AuditFactory
from teams.tests.factories import TeamFactory
from test_helpers.clients import DataTestClient
from users.enums import UserType
from users.tests.factories import GovUserFactory, ExporterUserFactory


class CasesAuditTrailSearchTestCase(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.team = TeamFactory()
        self.gov_user = GovUserFactory(team=self.team)
        self.exporter_user = ExporterUserFactory()

    def test_filter_by_gov_user(self):
        audit = AuditFactory(actor=self.gov_user, target=self.case.get_case())

        case_filters = get_case_activity_filters(self.case.id)

        actions = [{"key": audit.verb.value, "value": audit.verb.human_readable()}]
        teams = [{"value": self.team.name, "key": str(self.team.id)}]
        users = [{"value": f"{self.gov_user.first_name} {self.gov_user.last_name}", "key": str(self.gov_user.id)}]
        user_types = [
            {"key": UserType.INTERNAL.value, "value": UserType.INTERNAL.human_readable()},
            {"key": UserType.EXPORTER.value, "value": UserType.EXPORTER.human_readable()},
        ]

        self.assertEqual(case_filters["activity_types"], actions)
        self.assertEqual(case_filters["teams"], teams)
        self.assertEqual(case_filters["users"], users)
        self.assertEqual(case_filters["user_types"], user_types)

        # Create new audit with exporter
        AuditFactory(actor=self.exporter_user, target=self.case.get_case())

        case_filters = get_case_activity_filters(self.case.id)

        self.assertEqual(case_filters["users"].sort(key=lambda x: x["key"]), users.sort(key=lambda x: x["key"]))
