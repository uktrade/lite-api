from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class CasesResponseTests(EndPointTests):

    url = "/cases/"

    def test_cases_list(self):
        self.call_endpoint(self.get_gov_user(), self.url, is_gov=True)

    def test_case_destination(self):
        self.call_endpoint(self.get_gov_user(), self.url + "destination/GB/", is_gov=True)

    def test_cases_detail(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id(), is_gov=True)

    def test_case_notes(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/case-notes/", is_gov=True)

    def test_case_officers(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/case-officer/", is_gov=True)

    def test_case_activity(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/activity/", is_gov=True)

    def test_case_additional_contacts(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/additional-contacts/", is_gov=True)

    def test_cases_user_advice(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/user-advice/", is_gov=True)

    def test_cases_team_advice(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/team-advice/", is_gov=True)

    def test_cases_final_advice(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/final-advice/", is_gov=True)

    def test_cases_view_final_advice(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/view-final-advice/", is_gov=True)

    def test_cases_final_advice_documents(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/final-advice-documents/", is_gov=True)

    def test_cases_goods_countries_decisions(self):
        self.call_endpoint(
            self.get_gov_user(), self.url + self.get_case_id() + "/goods-countries-decisions/", is_gov=True
        )

    def test_cases_generated_documents(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/generated-documents/", is_gov=True)

    def test_cases_finalise(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/finalise/", is_gov=True)

    def test_cases_documents_list(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/documents/", is_gov=True)

    def test_cases_documents_detail(self):
        self.call_endpoint(
            self.get_gov_user(),
            self.url + self.get_case_id() + "/documents/" + self.get_case_document()["s3_key"],
            is_gov=True,
        )

    def test_cases_documents_download(self):
        self.call_endpoint(
            self.get_gov_user(),
            self.url + self.get_case_id() + "/documents/" + self.get_case_document()["id"],
            is_gov=True,
        )

    def test_cases_ecju_queries(self):
        self.call_endpoint(self.get_gov_user(), self.url + self.get_case_id() + "/ecju-queries/", is_gov=True)

    def test_cases_ecju_query(self):
        self.call_endpoint(
            self.get_gov_user(),
            self.url + self.get_case_id() + "/ecju-queries/" + self.get_ecju_query_id(),
            is_gov=True,
        )
