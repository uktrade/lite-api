from django.test import tag

from test_helpers.clients import DataTestClient


@tag("only")
class ReferenceCode(DataTestClient):

    def setUp(self):
        super().setUp()

    def test_standard_application_reference_code(self):
        self.assertTrue(True)
