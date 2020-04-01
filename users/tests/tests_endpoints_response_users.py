from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class UserResponseTests(EndPointTests):
    url = "/users/"

    def test_users_list(self):
        self.call_endpoint(self.get_exporter(), self.url)

    def test_users_detail(self):
        self.call_endpoint(self.get_exporter(), self.url + self.get_users_id())

    def test_users_me(self):
        self.call_endpoint(self.get_exporter(), self.url + "me/")

    def test_users_notifications(self):
        self.call_endpoint(self.get_exporter(), self.url + "notifications/")
