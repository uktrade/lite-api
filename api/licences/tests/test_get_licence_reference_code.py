from string import ascii_lowercase, ascii_uppercase

from api.licences.enums import LicenceStatus
from api.licences.helpers import get_licence_reference_code
from test_helpers.clients import DataTestClient


class GetLicenceReferenceCodeTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)

    def test_get_first_licence_reference_code(self):
        """
        Check the first licence reference code matches the application reference
        """
        reference_code = get_licence_reference_code(self.application.reference_code)

        self.assertEqual(reference_code, self.application.reference_code)

    def test_get_amended_licence_old_reference_code_format(self):
        """
        Check all amended licences get suffix '/A' -> '/Z' in the old format
        """
        self.application.reference_code = "GBSIEL/2021/0000001/P"
        self.application.save()

        for letter in ascii_uppercase:
            self.create_licence(self.application, status=LicenceStatus.ISSUED)
            reference_code = get_licence_reference_code(self.application.reference_code)
            self.assertEqual(reference_code, f"{self.application.reference_code}/{letter}")

    def test_get_amended_licence_reference_code(self):
        """
        Check all amended licences get suffix '-01', '-02', '-03' etc.
        """
        for number in range(100, 1):
            self.create_licence(self.application, status=LicenceStatus.ISSUED)
            reference_code = get_licence_reference_code(self.application.reference_code)
            self.assertEqual(reference_code, f"{self.application.reference_code}-{number:02}")
