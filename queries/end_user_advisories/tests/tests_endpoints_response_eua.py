from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class EUAResponseTests(EndPointTests):

    url = "/queries/end-user-advisories/"

    def test_end_user_advisory_list(self):
        self.call_endpoint(self.get_exporter(), self.url)

    def test_end_user_advisory_details(self):
        self.call_endpoint(self.get_exporter(), self.url + self.get_end_user_advisory_id())
