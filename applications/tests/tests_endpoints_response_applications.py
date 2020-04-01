from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class ApplicationResponseTests(EndPointTests):
    url = "/applications/"

    def test_application_list(self):
        self.call_endpoint(self.get_exporter(), self.url)

    def test_application_detail(self):
        self.call_endpoint(self.get_exporter(), self.url + self.get_standard_application()["id"])

    def test_application_goods(self):
        self.call_endpoint(
            self.get_exporter(), self.url + self.get_standard_application()["id"] + "/goods/",
        )

    def test_applications_goodstype_list(self):
        self.call_endpoint(
            self.get_exporter(), self.url + self.get_open_application()["id"] + "/goodstypes/",
        )

    def test_applications_goodstype_detail(self):
        self.call_endpoint(
            self.get_exporter(),
            self.url + self.get_open_application()["id"] + "/goodstypes/" + self.get_application_goodstype_id(),
        )

    def test_applications_goodstype_documents(self):
        self.call_endpoint(
            self.get_exporter(),
            self.url
            + self.get_open_application()["id"]
            + "/goodstypes/"
            + self.get_application_goodstype_id()
            + "/document/",
        )

    def test_application_parties_list(self):
        self.call_endpoint(
            self.get_exporter(), self.url + self.get_standard_application()["id"] + "/parties/",
        )

    def test_application_parties_details(self):
        self.call_endpoint(
            self.get_exporter(),
            self.url + self.get_standard_application()["id"] + "/parties/" + self.get_party_on_application_id(),
        )

    def test_application_parties_document(self):
        self.call_endpoint(
            self.get_exporter(),
            self.url
            + self.get_standard_application()["id"]
            + "/parties/"
            + self.get_party_on_application_id()
            + "/document/",
        )

    def test_application_sites(self):
        self.call_endpoint(self.get_exporter(), self.url + self.get_standard_application()["id"] + "/sites/")

    def test_application_external_locations(self):
        self.call_endpoint(
            self.get_exporter(), self.url + self.get_standard_application()["id"] + "/external_location/"
        )

    def test_application_countries(self):
        self.call_endpoint(self.get_exporter(), self.url + self.get_standard_application()["id"] + "/countries/")
