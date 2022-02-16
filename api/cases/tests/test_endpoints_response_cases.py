from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class CasesResponseTests(EndPointTests):
    url = "/cases/"

    def test_cases_list(self):
        self.call_endpoint(self.get_gov_headers(), self.url)

    def test_case_destination(self):
        self.call_endpoint(self.get_gov_headers(), self.url + "destinations/GB/")

    def test_cases_detail(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id())

    def test_case_notes(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/case-notes/")

    def test_case_officers(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/case-officer/")

    def test_case_activity(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/activity/")

    def test_case_additional_contacts(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/additional-contacts/")

    def test_cases_user_advice(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/user-advice/")

    def test_cases_team_advice(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/team-advice/")

    def test_cases_final_advice(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/final-advice/")

    def test_cases_final_advice_documents(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/final-advice-documents/")

    def test_cases_goods_countries_decisions(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/goods-countries-decisions/")

    def test_cases_generated_documents(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/generated-documents/")

    def test_cases_finalise(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/finalise/")

    def test_cases_documents_list(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/documents/")

    def test_cases_documents_detail(self):
        self.call_endpoint(
            self.get_gov_headers(),
            self.url + self.get_case_id() + "/documents/" + self.get_case_document()["s3_key"],
        )

    def test_cases_documents_download(self):
        self.call_endpoint(
            self.get_gov_headers(),
            self.url + self.get_case_id() + "/documents/" + self.get_case_document()["id"],
        )

    def test_cases_ecju_queries(self):
        self.call_endpoint(self.get_gov_headers(), self.url + self.get_case_id() + "/ecju-queries/")

    def test_cases_ecju_query(self):
        self.call_endpoint(
            self.get_gov_headers(),
            self.url + self.get_case_id() + "/ecju-queries/" + self.get_case_ecju_query_id(),
        )

    def test_export_enforcement_xml(self):
        self.call_endpoint(
            self.get_gov_headers(),
            self.url + "enforcement-check/" + self.get_queue_id(),
        )
