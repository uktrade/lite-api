from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class FlagsResponseTests(EndPointTests):
    url = "/flags/"

    def test_flags_list(self):
        self.call_endpoint(self.get_gov_headers(), self.url)

    def test_flags_detail(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_flag_id())
