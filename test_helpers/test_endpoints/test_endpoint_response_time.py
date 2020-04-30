import datetime
import csv

from django.test import SimpleTestCase, tag
from cases.enums import CaseTypeEnum
from conf.settings import env
from test_helpers.test_endpoints.client import get
from test_helpers.test_endpoints.user_setup import login_exporter, login_internal


csv_data = [["date_time", datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")]]


@tag("performance", "endpoints-performance")
class EndPointTests(SimpleTestCase):
    """
    Class to run tests against different endpoints, to determine their response times.
    Will output a csv with the urls and response times.
    """

    # request headers
    exporter = None
    gov_user = None

    # output variables
    time = None
    appended_address = None

    # stored variables for requests, so no need to get the data multiple times across tests
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
    routing_rule_id = None

    def call_endpoint(self, user, appended_address, save_results=True):
        response = get(user, appended_address)

        if save_results:
            # if save is set this is the final endpoint we wish to hit, and we want to store the time against
            self.appended_address = appended_address
            self.time = response.elapsed.total_seconds()

        return response

    @classmethod
    def setUpClass(cls):
        if len(csv_data) <= 2:
            # set up headers data in csv if not already done
            csv_data.append(["env", env("PERFORMANCE_TEST_HOST")])
            csv_data.append([])
            csv_data.append(["url", "response_time"])

        super().setUpClass()

    def tearDown(self):
        if self.time:
            csv_data.append([self.appended_address, self.time])
        else:
            csv_data.append([self._testMethodName, "Error"])

        # print out the function and time function took to run
        print("\n" + self._testMethodName + ", " + str(self.time) if self.time else "Error")

        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        with open("test_helpers/test_endpoints/results/" + csv_data[0][1] + ".csv", "w", newline="\n") as file:
            # write a new csv file named after the current date, outputting all the times for each case
            writer = csv.writer(file)
            writer.writerows(csv_data)

        super().tearDownClass()

    def get_exporter(self):
        """
        Will try and get or fetch the exporter headers
        :return: exporter headers
        """
        if not self.exporter:
            self.exporter = login_exporter()
        return self.exporter

    def get_gov_user(self):
        """
        Will try and get or fetch the gov user headers
        :return: gov user headers
        """
        if not self.gov_user:
            self.gov_user = login_internal()
        return self.gov_user

    def get_standard_application(self):
        """
        Function to get or fetch a standard applications id.
        If id is not already set, will request against the "/applications/"
            endpoint one page at a time until it gets one.
        :return: standard_application_id
        """
        if not self.standard_application_id:
            self._get_application_by_case_type(CaseTypeEnum.SIEL.sub_type, "standard_application_id")

        return self.standard_application_id

    def get_open_application(self):
        """
        Function to get or fetch a open applications id.
        If id is not already set, will request against the "/applications/"
            endpoint one page at a time until it gets one.
        :return: open_application_id
        """
        if not self.open_application_id:
            self._get_application_by_case_type(CaseTypeEnum.OIEL.sub_type, "open_application_id")

        return self.open_application_id

    def _get_application_by_case_type(self, case_type, attribute):
        response = self.call_endpoint(self.get_exporter(), "/applications/", save_results=False).json()
        for page in range(0, response["total_pages"]):
            for application in response["results"]:
                if application["case_type"]["sub_type"]["key"] == case_type:
                    self.__setattr__(attribute, application)
                    break
            else:
                response = self.call_endpoint(
                    self.get_exporter(), "/applications/page=" + str(page + 1), save_results=False
                ).json()
                continue

            break

    def get_application_goodstype_id(self):
        if not self.goods_type_id:
            response = self.call_endpoint(
                self.get_exporter(),
                "/applications/" + self.get_open_application()["id"] + "/goodstypes/",
                save_results=False,
            )
            self.goods_type_id = response.json()["goods"][0]["id"]

        return self.goods_type_id

    def get_party_on_application_id(self):
        if not self.application_party_id:
            response = self.call_endpoint(
                self.get_exporter(),
                "/applications/" + self.get_standard_application()["id"] + "/parties/",
                save_results=False,
            )

            self.application_party_id = response.json()["parties"][0]["id"]

        return self.application_party_id

    def get_good_id(self):
        if not self.good_id:
            response = self.call_endpoint(self.get_exporter(), "/goods/", save_results=False)

            self.good_id = response.json()["results"][0]["id"]

        return self.good_id

    def get_good_document_id(self):
        if not self.good_document_id:
            response = self.call_endpoint(
                self.get_exporter(), "/goods/" + self.get_good_id() + "/documents/", save_results=False
            )

            self.good_document_id = response.json()["documents"][0]["id"]
        return self.good_document_id

    def get_organisation_user_id(self):
        if not self.organisation_user_id:
            response = self.call_endpoint(
                self.get_exporter(),
                "/organisations/" + self.get_exporter()["ORGANISATION-ID"] + "/users/",
                save_results=False,
            )

            self.organisation_user_id = response.json()["results"][0]["id"]

        return self.organisation_user_id

    def get_organisation_role_id(self):
        if not self.organisation_role_id:
            response = self.call_endpoint(
                self.get_exporter(),
                "/organisations/" + self.get_exporter()["ORGANISATION-ID"] + "/roles/",
                save_results=False,
            )

            self.organisation_role_id = response.json()["results"][0]["id"]

        return self.organisation_role_id

    def get_organisation_site_id(self):
        if not self.organisation_site_id:
            response = self.call_endpoint(
                self.get_exporter(),
                "/organisations/" + self.get_exporter()["ORGANISATION-ID"] + "/sites/",
                save_results=False,
            )

            self.organisation_site_id = response.json()["sites"][0]["id"]

        return self.organisation_site_id

    def get_end_user_advisory_id(self):
        if not self.end_user_advisory_id:
            response = self.call_endpoint(self.get_exporter(), "/queries/end-user-advisories/", save_results=False)

            self.end_user_advisory_id = response.json()["results"][0]["id"]

        return self.end_user_advisory_id

    def get_users_id(self):
        if not self.users_id:
            response = self.call_endpoint(self.get_exporter(), "/users/", save_results=False)

            self.users_id = response.json()["users"][0]["id"]

        return self.users_id

    def get_team_id(self):
        if not self.team_id:
            response = self.call_endpoint(self.get_gov_user(), "/teams/", save_results=False)

            self.team_id = response.json()["teams"][0]["id"]

        return self.team_id

    def get_queue_id(self):
        if not self.queue_id:
            response = self.call_endpoint(self.get_gov_user(), "/queues/", save_results=False)

            self.queue_id = response.json()["queues"][0]["id"]

        return self.queue_id

    def get_picklist_id(self):
        if not self.picklist_id:
            response = self.call_endpoint(self.get_gov_user(), "/picklist/", save_results=False)

            self.picklist_id = response.json()["picklist_items"][0]["id"]

        return self.picklist_id

    def get_letter_template_id(self):
        if not self.letter_template_id:
            response = self.call_endpoint(self.get_gov_user(), "/letter-templates/", save_results=False)

            self.letter_template_id = response.json()["results"][0]["id"]

        return self.letter_template_id

    def get_gov_user_id(self):
        if not self.gov_user_id:
            response = self.call_endpoint(self.get_gov_user(), "/gov-users/", save_results=False)

            self.gov_user_id = response.json()["results"][0]["id"]

        return self.gov_user_id

    def get_gov_user_role_id(self):
        if not self.gov_user_role_id:
            response = self.call_endpoint(self.get_gov_user(), "/gov-users/roles/", save_results=False)

            self.gov_user_role_id = response.json()["roles"][0]["id"]

        return self.gov_user_role_id

    def get_flag_id(self):
        if not self.flag_id:
            response = self.call_endpoint(self.get_gov_user(), "/flags/", save_results=False)

            self.flag_id = response.json()["flags"][0]["id"]

        return self.flag_id

    def get_flagging_rules_id(self):
        if not self.flagging_rule_id:
            response = self.call_endpoint(self.get_gov_user(), "/flags/rules/", save_results=False)

            self.flagging_rule_id = response.json()["results"][0]["id"]

        return self.flagging_rule_id

    def get_case_id(self):
        if not self.case_id:
            response = self.call_endpoint(self.get_gov_user(), "/cases/", save_results=False)

            self.case_id = response.json()["results"]["cases"][0]["id"]

        return self.case_id

    def get_case_document(self):
        if not self.case_document:
            response = self.call_endpoint(
                self.get_gov_user(), "/cases/" + self.get_case_id() + "/documents/", save_results=False
            )
            self.case_document = response.json()["documents"][0]

        return self.case_document

    def get_case_ecju_query_id(self):
        if not self.case_ecju_query_id:
            response = self.call_endpoint(
                self.get_gov_user(), self.url + self.get_case_id() + "/ecju-queries/", save_results=False
            )

            self.case_ecju_query_id = response.json()["ecju_queries"][0]["id"]

        return self.case_ecju_query_id

    def get_routing_rule_id(self):
        if not self.routing_rule_id:
            response = self.call_endpoint(self.get_gov_user(), "/routing-rules/", save_results=False)

            self.routing_rule_id = response.json()["results"][0]["id"]

        return self.routing_rule_id
