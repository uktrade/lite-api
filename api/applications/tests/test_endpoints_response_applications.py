from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class ApplicationResponseTests(EndPointTests):
    url = "/applications/"

    def test_application_list(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)

    def test_application_detail(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + self.get_standard_application()["id"])

    def test_application_activity(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/activity/")

    def test_application_countries(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/countries/"
        )

    def test_application_documents(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/documents/"
        )

    def test_application_duration(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/duration/")

    def test_application_existing(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + "existing/")

    def test_application_existing_parties(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + "existing-parties/")

    def test_application_external_location(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/external_location/"
        )

    def test_application_final_decision(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/final-decision/"
        )

    def test_application_goods(self):
        self.call_endpoint(
            self.get_exporter_headers(),
            self.url + self.get_standard_application()["id"] + "/goods/",
        )

    def test_application_parties_list(self):
        self.call_endpoint(
            self.get_exporter_headers(),
            self.url + self.get_standard_application()["id"] + "/parties/",
        )

    def test_application_parties_details(self):
        self.call_endpoint(
            self.get_exporter_headers(),
            self.url + self.get_standard_application()["id"] + "/parties/" + self.get_party_on_application_id(),
        )

    def test_application_parties_copy(self):
        self.call_endpoint(
            self.get_exporter_headers(),
            self.url
            + self.get_standard_application()["id"]
            + "/parties/"
            + self.get_party_on_application_id()
            + "/copy/",
        )

    def test_application_parties_document(self):
        self.call_endpoint(
            self.get_exporter_headers(),
            self.url
            + self.get_standard_application()["id"]
            + "/parties/"
            + self.get_party_on_application_id()
            + "/document/",
        )

    def test_application_sites(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/sites/")

    def test_application_external_locations(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/external_locations/"
        )
