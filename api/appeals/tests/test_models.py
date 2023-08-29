from test_helpers.clients import DataTestClient

from .factories import AppealFactory


class AppealTest(DataTestClient):
    def test_deleting_appeal_retains_related_application(self):
        appeal = AppealFactory()

        application = self.create_standard_application_case(self.organisation)

        application.appeal = appeal
        application.save()

        appeal.delete()

        application.refresh_from_db()
