from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class LetterTemplatesResponseTests(EndPointTests):
    url = "/letter-templates/"

    def test_letter_templates_list(self):
        self.call_endpoint(self.get_gov_headers(), self.url)

    def test_letter_templates_detail(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_letter_template_id())
