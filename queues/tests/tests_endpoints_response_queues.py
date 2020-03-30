from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class QueuesResponseTests(EndPointTests):

    url = "/queues/"

    def test_queues_list(self):
        self.call_endpoint(self.get_gov_user(), self.url, is_gov=True)

    def test_queues_detail(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_queue_id(), is_gov=True)

    def test_queues_assignments(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_queue_id() + "/case-assignments/", is_gov=True)
