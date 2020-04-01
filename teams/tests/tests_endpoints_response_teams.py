from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class TeamsResponseTests(EndPointTests):

    url = "/teams/"

    def test_teams_list(self):
        self.call_endpoint(self.get_gov_user(), self.url)

    def test_team_detail(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_team_id())

    def test_teams_users(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_team_id() + "/users/")
