from freezegun import freeze_time

from test_helpers.clients import DataTestClient

from api.applications.enums import ApplicationExportType
from api.applications.tests.factories import (
    DraftStandardApplicationFactory,
    StandardApplicationFactory,
)


@freeze_time("2023-11-03 12:00:00")
class ReferenceCode(DataTestClient):
    def test_permanent_standard_application_reference_code(self):
        standard_application = StandardApplicationFactory(export_type=ApplicationExportType.PERMANENT)

        self.assertEqual(
            standard_application.reference_code,
            "GBSIEL/2023/0000001/P",
        )

    def test_temporary_standard_application_reference_code(self):
        standard_application = StandardApplicationFactory(export_type=ApplicationExportType.TEMPORARY)

        self.assertEqual(
            standard_application.reference_code,
            "GBSIEL/2023/0000001/T",
        )

    def test_draft_applications_dont_have_reference_codes(self):
        draft = DraftStandardApplicationFactory()

        self.assertIsNone(draft.reference_code)

    def test_reference_code_increment(self):
        standard_application_1 = StandardApplicationFactory(export_type=ApplicationExportType.PERMANENT)
        standard_application_2 = StandardApplicationFactory(export_type=ApplicationExportType.PERMANENT)

        self.assertEqual(standard_application_1.reference_code, "GBSIEL/2023/0000001/P")
        self.assertEqual(standard_application_2.reference_code, "GBSIEL/2023/0000002/P")
