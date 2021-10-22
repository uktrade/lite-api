from django.core.management import call_command

from test_helpers.clients import DataTestClient


class ChangeCaseStatusMgmtCommandTests(DataTestClient):
    def test_case_status_change_command(self):
        self.application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.application)
        self.assertEqual(self.application.status.status, "submitted")

        call_command("change_case_status", self.application.reference_code, "finalised")
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, "finalised")

    def test_case_status_change_command_dry_run(self):
        self.application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.application)
        self.assertEqual(self.application.status.status, "submitted")

        call_command("change_case_status", self.application.reference_code, "finalised", "--dry_run")
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, "submitted")
