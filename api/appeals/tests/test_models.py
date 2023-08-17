from test_helpers.clients import DataTestClient

from ..factories import Appeal


class AppealTest(DataTestClient):
    def test_deleting_appeal_retains_related_application(self):
        appeal = Appeal()

        application = self.create_standard_application_case(self.organisation)

        application.appeal = appeal
        application.save()

        appeal.delete()

        application.refresh_from_db()
