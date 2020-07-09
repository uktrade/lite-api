from string import ascii_uppercase

from licences.enums import LicenceStatus
from licences.helpers import get_licence_reference_code
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

    def test_get_amended_licence_reference_code(self):
        """
        Check all amended licences get suffix /A -> /Z
        """
        for letter in ascii_uppercase:
            self.create_licence(self.application, status=LicenceStatus.ISSUED)
            reference_code = get_licence_reference_code(self.application.reference_code)
            self.assertEqual(reference_code, self.application.reference_code + "/" + letter)
