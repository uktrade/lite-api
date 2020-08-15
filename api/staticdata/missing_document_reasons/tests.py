# TODO: implement test for getting missing document reasons
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class MissingDocumentReasonsResponseTests(EndPointTests):
    url = "/static/missing-document-reasons/"

    def test_missing_document_reasons(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)
