from string import ascii_uppercase

from api.licences.enums import LicenceStatus
from api.licences.helpers import get_licence_reference_code
from api.licences.tests.factories import StandardLicenceFactory
from test_helpers.clients import DataTestClient


class GetLicenceReferenceCodeTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)

    def test_get_first_licence_reference_code(self):
        """
        Check the first licence reference code matches the application reference
        with a suffix
        """
        reference_code = get_licence_reference_code(self.application.reference_code)

        self.assertEqual(reference_code, f"{self.application.reference_code}")

    def test_get_amended_licence_reference_code(self):
        """
        Check all amended licences get suffix /A -> /Z
        """
        for letter in ascii_uppercase:
            StandardLicenceFactory(case=self.application, status=LicenceStatus.ISSUED)
            reference_code = get_licence_reference_code(self.application.reference_code)
            self.assertEqual(reference_code, self.application.reference_code + "/" + letter)
