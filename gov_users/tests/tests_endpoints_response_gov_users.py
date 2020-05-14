from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class GovUsersResponseTests(EndPointTests):
    url = "/gov-users/"

    def test_gov_users_list(self):
        self.call_endpoint(self.get_gov_headers(), self.url)

    def test_gov_users_detail(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_gov_user_id())

    def test_roles_list(self):
        self.call_endpoint(self.get_gov_headers(), self.url + "roles/")

    def test_roles_detail(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_gov_user_role_id())

    def test_permissions(self):
        self.call_endpoint(self.get_gov_headers(), self.url + "permissions/")

    def test_me(self):
        self.call_endpoint(self.get_gov_headers(), self.url + "me/")
