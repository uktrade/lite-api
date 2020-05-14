from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class ApplicationResponseTests(EndPointTests):
    url = "/applications/"

    def test_application_list(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)

    def test_application_detail(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + self.get_standard_application()["id"])

    def test_application_goods(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/goods/",
        )

    def test_applications_goodstype_list(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_open_application()["id"] + "/goodstypes/",
        )

    def test_applications_goodstype_detail(self):
        application = self.get_open_application()
        application_id = application["id"]
        goods_type = self.get_application_goodstype_id()
        url = f"{self.url}{application_id}/goodstype/{goods_type}"
        exporter_user = self.get_exporter_headers()
        self.call_endpoint(exporter_user, url)

    def test_applications_goodstype_documents(self):
        self.call_endpoint(
            self.get_exporter_headers(),
            self.url
            + self.get_open_application()["id"]
            + "/goodstype/"
            + self.get_application_goodstype_id()
            + "/document/",
        )

    def test_application_parties_list(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/parties/",
        )

    def test_application_parties_details(self):
        self.call_endpoint(
            self.get_exporter_headers(),
            self.url + self.get_standard_application()["id"] + "/parties/" + self.get_party_on_application_id(),
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

    def test_application_countries(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_standard_application()["id"] + "/countries/"
        )
