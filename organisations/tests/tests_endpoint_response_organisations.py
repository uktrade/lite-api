from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class OrganisationResponseTests(EndPointTests):

    url = "/organisations/"

    def test_organisation_users_list(self):
        self.call_endpoint(self.get_exporter(), self.url + self.get_exporter()["organisation-id"] + "/users/")

    def test_organisation_users_detail(self):
        self.call_endpoint(
            self.get_exporter(),
            self.url + self.get_exporter()["organisation-id"] + "/users/" + self.get_organisation_user_id(),
        )

    def test_organisation_sites_list(self):
        self.call_endpoint(self.get_exporter(), self.url + self.get_exporter()["organisation-id"] + "/sites/")

    def test_organisation_sites_detail(self):
        self.call_endpoint(
            self.get_exporter(),
            self.url + self.get_exporter()["organisation-id"] + "/sites/" + self.get_organisation_site_id(),
        )

    def test_organisation_external_locations(self):
        self.call_endpoint(
            self.get_exporter(), self.url + self.get_exporter()["organisation-id"] + "/external_locations/",
        )

    def test_organisation_roles_list(self):
        self.call_endpoint(self.get_exporter(), self.url + self.get_exporter()["organisation-id"] + "/roles/")

    def test_organisation_roles_detail(self):
        self.call_endpoint(
            self.get_exporter(),
            self.url + self.get_exporter()["organisation-id"] + "/roles/" + self.get_organisation_role_id(),
        )
