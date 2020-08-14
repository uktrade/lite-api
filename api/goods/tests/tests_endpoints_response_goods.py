from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class GoodResponseTests(EndPointTests):
    url = "/goods/"

    def test_goods_list(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)

    def test_good_detail(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + self.get_good_id())

    def test_good_documents_list(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + self.get_good_id() + "/documents/")

    def test_good_documents_details(self):
        self.call_endpoint(
            self.get_exporter_headers(), self.url + self.get_good_id() + "/documents/" + self.get_good_document_id()
        )
