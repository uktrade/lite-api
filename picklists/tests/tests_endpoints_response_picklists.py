from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class PicklistsResponseTests(EndPointTests):
    url = "/picklist/"

    def test_picklist_list(self):
        self.call_endpoint(self.get_gov_user(), self.url)

    def test_picklist_detail(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_picklist_id())
