import datetime
import csv

from django.test import SimpleTestCase, tag
from cases.enums import CaseTypeEnum
from conf.settings import env
from test_helpers.test_endpoints.client import get
from test_helpers.test_endpoints.user_setup import login_exporter, login_internal


times = [["date_time", datetime.datetime.now().strftime("%d-%m-%Y_%H:%M:%S")]]


@tag("performance", "endpoints-performance")
class EndPointTests(SimpleTestCase):
    csv = None
    exporter = None
    gov_user = None
    time = None
    appended_address = None

    standard_application_id = None
    open_application_id = None
    goods_type_id = None
    application_party_id = None
    good_id = None
    good_document_id = None
    organisation_user_id = None
    organisation_role_id = None
    organisation_site_id = None
    end_user_advisory_id = None
    users_id = None
    team_id = None
    queue_id = None
    picklist_id = None
    letter_template_id = None
    gov_user_id = None
    gov_user_role_id = None
    flag_id = None
    flagging_rule_id = None
    case_id = None
    case_document = None
    case_ecju_query_id = None

    def call_endpoint(self, user, appended_address, is_gov=False, save=True):
        response = get(user, appended_address, is_gov)

        if save:
            # TODO: move appended address allocation into each test
            self.appended_address = appended_address
            self.time = response.elapsed.total_seconds()

        return response

    @classmethod
    def setUpClass(cls):
        if len(times) <= 2:
            times.append(["env", env("PERFORMANCE_TEST_HOST")])
            times.append([])
            times.append(["url", "response_time"])

        super().setUpClass()

    def tearDown(self):
        if self.time:
            times.append([self.appended_address, self.time])
        else:
            times.append([self._testMethodName, "Error"])

        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        with open("test_helpers/test_endpoints/results/" + times[0][1] + ".csv", "w", newline="\n") as file:
            writer = csv.writer(file)
            writer.writerows(times)

        super().tearDownClass()

    def get_exporter(self):
        if not self.exporter:
            self.exporter = login_exporter()
        return self.exporter

    def get_gov_user(self):
        if not self.gov_user:
            self.gov_user = login_internal()
        return self.gov_user

    def get_standard_application(self):
        if not self.standard_application_id:
            response = self.call_endpoint(self.get_exporter(), "/applications/", save=False).json()
            for page in range(1, response["total_pages"]):
                for application in response["results"]:
                    if application["case_type"]["reference"]["key"] == CaseTypeEnum.SIEL.reference:
                        self.standard_application_id = application
                        break
                else:
                    # TODO: get next page
                    continue

                break

        return self.standard_application_id

    def get_open_application(self):
        if not self.open_application_id:
            response = self.call_endpoint(self.get_exporter(), "/applications/", save=False).json()
            for page in range(1, response["total_pages"]):
                for application in response["results"]:
                    if application["case_type"]["reference"]["key"] == CaseTypeEnum.OIEL.reference:
                        self.open_application_id = application
                        break
                else:
                    # TODO: get next page
                    continue

                break

        return self.open_application_id

    def get_application_goodstype_id(self):
        if not self.goods_type_id:
            response = self.call_endpoint(
                self.get_exporter(), "/applications/" + self.get_open_application()["id"] + "/goodstypes/", save=False
            )
            self.goods_type_id = response.json()["goods"][0]["id"]

        return self.goods_type_id

    def get_party_on_application_id(self):
        if not self.application_party_id:
            response = self.call_endpoint(
                self.get_exporter(), "/applications/" + self.get_standard_application()["id"] + "/parties/", save=False
            )

            self.application_party_id = response.json()["parties"][0]["id"]

        return self.application_party_id

    def get_good_id(self):
        if not self.good_id:
            response = self.call_endpoint(self.get_exporter(), "/goods/", save=False)

            self.good_id = response.json()["results"][0]["id"]

        return self.good_id

    def get_good_document_id(self):
        if not self.good_document_id:
            response = self.call_endpoint(
                self.get_exporter(), "/goods/" + self.get_good_id() + "/documents/", save=False
            )

            self.good_document_id = response.json()["documents"][0]["id"]
        return self.good_document_id

    def get_organisation_user_id(self):
        if not self.organisation_user_id:
            response = self.call_endpoint(
                self.get_exporter(), "/organisations/" + self.get_exporter()["organisation-id"] + "/users/", save=False
            )

            self.organisation_user_id = response.json()["results"]["users"][0]["id"]

        return self.organisation_user_id

    def get_organisation_role_id(self):
        if not self.organisation_role_id:
            response = self.call_endpoint(
                self.get_exporter(), "/organisations/" + self.get_exporter()["organisation-id"] + "/roles/", save=False
            )

            self.organisation_role_id = response.json()["results"][0]["id"]

        return self.organisation_role_id

    def get_organisation_site_id(self):
        if not self.organisation_site_id:
            response = self.call_endpoint(
                self.get_exporter(), "/organisations/" + self.get_exporter()["organisation-id"] + "/sites/", save=False
            )

            self.organisation_site_id = response.json()["sites"][0]["id"]

        return self.organisation_site_id

    def get_end_user_advisory_id(self):
        if not self.end_user_advisory_id:
            response = self.call_endpoint(self.get_exporter(), "/queries/end-user-advisories/", save=False)

            self.end_user_advisory_id = response.json()["end_user_advisories"][0]["id"]

        return self.end_user_advisory_id

    def get_users_id(self):
        if not self.users_id:
            response = self.call_endpoint(self.get_exporter(), "/users/", save=False)

            self.users_id = response.json()["users"][0]["id"]

        return self.users_id

    def get_team_id(self):
        if not self.team_id:
            response = self.call_endpoint(self.get_gov_user(), "/teams/", is_gov=True, save=False)

            self.team_id = response.json()["teams"][0]["id"]

        return self.team_id

    def get_queue_id(self):
        if not self.queue_id:
            response = self.call_endpoint(self.get_gov_user(), "/queues/", is_gov=True, save=False)

            self.queue_id = response.json()["queues"][0]["id"]

        return self.queue_id

    def get_picklist_id(self):
        if not self.picklist_id:
            response = self.call_endpoint(self.get_gov_user(), "/picklist/", is_gov=True, save=False)

            self.picklist_id = response.json()["picklist_items"][0]["id"]

        return self.picklist_id

    def get_letter_template_id(self):
        if not self.letter_template_id:
            response = self.call_endpoint(self.get_gov_user(), "/letter-templates/", is_gov=True, save=False)

            self.letter_template_id = response.json()["results"][0]["id"]

        return self.letter_template_id

    def get_gov_user_id(self):
        if not self.gov_user_id:
            response = self.call_endpoint(self.get_gov_user(), "/gov-users/", is_gov=True, save=False)

            self.gov_user_id = response.json()["results"][0]["id"]

        return self.gov_user_id

    def get_gov_user_role_id(self):
        if not self.gov_user_role_id:
            response = self.call_endpoint(self.get_gov_user(), "/gov-users/roles/", is_gov=True, save=False)

            self.gov_user_role_id = response.json()["roles"][0]["id"]

        return self.gov_user_role_id

    def get_flag_id(self):
        if not self.flag_id:
            response = self.call_endpoint(self.get_gov_user(), "/flags/", is_gov=True, save=False)

            self.flag_id = response.json()["flags"][0]["id"]

        return self.flag_id

    def get_flagging_rules_id(self):
        if not self.flagging_rule_id:
            response = self.call_endpoint(self.get_gov_user(), "/flags/rules/", is_gov=True, save=False)

            self.flagging_rule_id = response.json()["results"][0]["id"]

        return self.flagging_rule_id

    def get_case_id(self):
        if not self.case_id:
            response = self.call_endpoint(self.get_gov_user(), "/cases/", is_gov=True, save=False)

            self.case_id = response.json()["results"]["cases"][0]["id"]

        return self.case_id

    def get_case_document(self):
        if not self.case_document:
            response = self.call_endpoint(
                self.get_gov_user(), "/cases/" + self.get_case_id() + "/documents/", is_gov=True, save=False
            )
            self.case_document = response.json()["documents"][0]

        return self.case_document

    def get_case_ecju_query_id(self):
        if not self.case_ecju_query_id:
            response = self.call_endpoint(
                self.get_gov_user(), self.url + self.get_case_id() + "/ecju-queries/", is_gov=True, save=False
            )

            self.case_ecju_query_id = response.json()["ecju_queries"][0]["id"]

        return self.case_ecju_query_id
