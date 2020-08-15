from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class OpenGeneralLicencesResponseTests(EndPointTests):
    url = "open-general-licences/"

    def test_ogl_list(self):
        self.call_endpoint(self.get_gov_headers(), self.url)

    def test_ogl_details(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_open_general_licence_id())

    def test_ogl_activity(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_open_general_licence_id() + "/activity/")
