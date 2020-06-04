from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class QueuesResponseTests(EndPointTests):
    url = "/queues/"

    def test_queues_list(self):
        self.call_endpoint(self.get_gov_headers(), self.url)

    def test_queues_list_without_pagination(self):
        self.call_endpoint(self.get_gov_headers(), self.url + "?disable_pagination=True")

    def test_queues_list_without_pagination_and_system(self):
        self.call_endpoint(self.get_gov_headers(), self.url + "?include_system=True&disable_pagination=True")

    def test_queues_detail(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_queue_id())

    def test_queues_assignments(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_queue_id() + "/case-assignments/")
