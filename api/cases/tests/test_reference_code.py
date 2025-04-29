from freezegun import freeze_time

from test_helpers.clients import DataTestClient

from api.applications.enums import ApplicationExportType


@freeze_time("2023-11-03 12:00:00")
class ReferenceCode(DataTestClient):
    def test_standard_application_reference_code(self):
        standard_application = self.create_draft_standard_application(self.organisation)
        standard_application = self.submit_application(standard_application)

        self.assertEqual(
            standard_application.reference_code,
            "GBSIEL/2023/0000001/P",
        )

    def test_temporary_application_reference_code(self):
        standard_application = self.create_draft_standard_application(self.organisation)
        standard_application.export_type = ApplicationExportType.TEMPORARY
        self.submit_application(standard_application)

        self.assertEqual(
            standard_application.reference_code,
            "GBSIEL/2023/0000001/T",
        )

    def test_draft_applications_dont_have_reference_codes(self):
        draft = self.create_draft_standard_application(self.organisation)
        self.assertIsNone(draft.reference_code)

    def test_reference_code_increment(self):
        standard_application_1 = self.create_draft_standard_application(self.organisation)
        standard_application_1 = self.submit_application(standard_application_1)
        standard_application_2 = self.create_draft_standard_application(self.organisation)
        standard_application_2 = self.submit_application(standard_application_2)

        self.assertEqual(standard_application_1.reference_code, "GBSIEL/2023/0000001/P")
        self.assertEqual(standard_application_2.reference_code, "GBSIEL/2023/0000002/P")
