from api.licences.views.main import LicenceType
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class LicencesResponseTests(EndPointTests):
    url = "/licences/"

    def test_licences_list(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)

    def test_licences_list_standard_licences_only(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + "?licence_type=" + LicenceType.LICENCE)

    def test_licences_list_clearances_only(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + "?licence_type=" + LicenceType.CLEARANCE)

    def test_nlr_list(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + "nlrs/")
