from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class LetterTemplatesResponseTests(EndPointTests):

    url = "/flags/"

    def test_flags_list(self):
        self.call_endpoint(self.get_gov_user(), self.url, is_gov=True)

    def test_flags_detail(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_flag_id(), is_gov=True)

    def test_flagging_rules_list(self):
        self.call_endpoint(self.get_gov_user(), self.url + "rules/", is_gov=True)

    def test_flagging_rules_detail(self):
        self.call_endpoint(self.get_gov_user(), self.url + "rules/" + self.get_flagging_rules_id(), is_gov=True)
