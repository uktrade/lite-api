from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class GovUsersResponseTests(EndPointTests):

    url = "/gov-users/"

    def test_gov_users_list(self):
        self.call_endpoint(self.get_gov_user(), self.url, is_gov=True)

    def test_gov_users_detail(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_gov_user_id(), is_gov=True)

    def test_roles_list(self):
        self.call_endpoint(self.get_gov_user(), self.url + "roles/", is_gov=True)

    def test_roles_detail(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_gov_user_role_id(), is_gov=True)

    def test_permissions(self):
        self.call_endpoint(self.get_gov_user(), self.url + "permissions/", is_gov=True)

    def test_me(self):
        self.call_endpoint(self.get_gov_user(), self.url + "me/", is_gov=True)
