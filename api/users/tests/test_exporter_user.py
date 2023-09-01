from test_helpers.clients import DataTestClient


class ExporterUserTests(DataTestClient):
    def test_is_in_organisation(self):
        self.assertTrue(self.exporter_user.is_in_organisation(self.organisation))

        another_organisation = self.create_organisation_with_exporter_user()[0]
        self.assertFalse(self.exporter_user.is_in_organisation(another_organisation))
