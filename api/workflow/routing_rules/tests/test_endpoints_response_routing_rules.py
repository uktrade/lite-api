from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class RoutingRuleResponseTests(EndPointTests):
    url = "/routing-rules/"

    def test_routing_rules_list(self):
        self.call_endpoint(self.get_gov_headers(), self.url)

    def test_routing_rule_details(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_routing_rule_id())
