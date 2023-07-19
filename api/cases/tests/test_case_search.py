import datetime

from django.urls import reverse
from django import utils as django_utils
from parameterized import parameterized
from rest_framework import status

from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.applications.tests.factories import (
    DenialMatchOnApplicationFactory,
    DenialMatchFactory,
    GoodOnApplicationFactory,
    StandardApplicationFactory,
    SanctionMatchFactory,
    PartyOnApplicationFactory,
)
from api.cases.enums import AdviceLevel, AdviceType, CaseTypeEnum
from api.cases.models import Case, CaseAssignment, EcjuQuery, CaseType
from api.flags.models import Flag
from api.flags.enums import FlagLevels
from api.goods.tests.factories import GoodFactory
from api.picklists.enums import PicklistType
from api.cases.tests.factories import CaseSIELFactory, FinalAdviceFactory
from api.queues.constants import (
    UPDATED_CASES_QUEUE_ID,
    SYSTEM_QUEUES,
    ALL_CASES_QUEUE_ID,
)
from api.queues.tests.factories import QueueFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.report_summaries.tests.factories import ReportSummaryPrefixFactory, ReportSummarySubjectFactory
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.users.tests.factories import GovUserFactory
from test_helpers.clients import DataTestClient
from api.users.enums import UserStatuses
from api.users.libraries.user_to_token import user_to_token
from api.users.models import GovUser

from lite_routing.routing_rules_internal.enums import FlagsEnum


class FilterAndSortTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("cases:search")
        statuses = [CaseStatusEnum.SUBMITTED, CaseStatusEnum.CLOSED, CaseStatusEnum.WITHDRAWN]

        self.application_cases = []
        for app_status in statuses:
            case = self.create_standard_application_case(self.organisation, "Example Application")
            case.status = get_case_status_by_status(app_status)
            case.save()
            self.queue.cases.add(case)
            self.queue.save()
            self.application_cases.append(case)

        self.clc_cases = []
        for clc_status in statuses:
            clc_query = self.create_clc_query("Example CLC Query", self.organisation)
            clc_query.status = get_case_status_by_status(clc_status)
            clc_query.save()
            self.queue.cases.add(clc_query)
            self.queue.save()
            self.clc_cases.append(clc_query)

    def test_get_cases_returns_only_system_and_users_team_queues(self):
        system_and_team_queue_ids = sorted([*SYSTEM_QUEUES.keys(), str(self.queue.id)])

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        queue_ids = sorted([queue["id"] for queue in response.json()["results"]["queues"]])

        self.assertEqual(queue_ids, system_and_team_queue_ids)

    def test_get_cases_no_filter_returns_all_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases with no filter
        Then all Cases are returned
        """
        all_cases = self.application_cases + self.clc_cases

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_cases), len(response_data["cases"]))
        self.assertEqual(
            [
                {"full_name": f"{user.first_name} {user.last_name}", "id": str(user.pk), "pending": user.pending}
                for user in GovUser.objects.filter(status=UserStatuses.ACTIVE)
            ],
            response_data["filters"]["gov_users"],
        )

    def test_get_app_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'Licence application'
        Then only Cases of that type are returned
        """
        url = f"{self.url}?case_type={CaseTypeEnum.SIEL.reference}"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.application_cases), len(response_data["cases"]))
        # Assert Case Type
        for case in response_data["cases"]:
            case_type_reference = Case.objects.filter(pk=case["id"]).values_list("case_type__reference", flat=True)[0]
            self.assertEqual(case_type_reference, CaseTypeEnum.SIEL.reference)

    def test_get_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'CLC query'
        Then only Cases of that type are returned
        """
        url = f"{self.url}?case_type={CaseTypeEnum.GOODS.reference}"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.clc_cases), len(response_data["cases"]))

        # Assert Case Type
        for case in response_data["cases"]:
            case_type_reference = Case.objects.filter(pk=case["id"]).values_list("case_type__reference", flat=True)[0]
            self.assertEqual(case_type_reference, CaseTypeEnum.GOODS.reference)

    def test_get_submitted_status_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'CLC query'
        Then only Cases of that type are returned
        """
        url = f"{self.url}?case_type={CaseTypeEnum.GOODS.reference}"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.clc_cases), len(response_data["cases"]))
        # Assert Case Type
        for case in response_data["cases"]:
            case_type_reference = Case.objects.filter(pk=case["id"]).values_list("case_type__reference", flat=True)[0]
            self.assertEqual(case_type_reference, CaseTypeEnum.GOODS.reference)

    def test_get_all_cases_queue_submitted_status_and_clc_type_cases(self):
        """
        Given multiple cases exist with different statuses and case-types
        When a user requests to view All Cases of type 'CLC query'
        Then only cases of that type are returned
        """
        case_status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        clc_submitted_cases = list(filter(lambda c: c.query.status == case_status, self.clc_cases))
        url = f'{reverse("cases:search")}?case_type={CaseTypeEnum.GOODS.reference}&status={case_status.status}'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clc_submitted_cases), len(response_data["cases"]))
        # Assert Case Type
        for case in response_data["cases"]:
            case_type_reference = Case.objects.filter(pk=case["id"]).values_list("case_type__reference", flat=True)[0]
            self.assertEqual(case_type_reference, CaseTypeEnum.GOODS.reference)

    def test_get_cases_filter_by_case_officer(self):
        """
        Given multiple cases exist with case officers attached and not attached
        When a user requests to view All Cases when the case officer is set to themselves
        Then only cases of that type are returned
        """
        self.application_cases[0].case_officer = self.gov_user
        self.application_cases[0].save()
        url = f'{reverse("cases:search")}?case_officer={self.gov_user.pk}'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.application_cases[0].id))

    def test_get_cases_filter_by_case_officer_not_assigned(self):
        """
        Given multiple cases exist with case officers attached and not attached
        When a user requests to view All Cases with no assigned case officer
        Then only cases without an assigned case officer are returned
        """
        all_cases = self.application_cases + self.clc_cases
        self.application_cases[0].case_officer = self.gov_user
        self.application_cases[0].save()
        url = f'{reverse("cases:search")}?case_officer=not_assigned'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(all_cases) - 1)
        assigned_case = str(self.application_cases[0].id)
        cases_returned = [x["id"] for x in response_data]
        self.assertNotIn(assigned_case, cases_returned)

    def test_get_cases_filter_by_assigned_user(self):
        """
        Given multiple cases exist with users assigned and not assigned
        When a user requests to view All Cases when the assigned user is set to themselves
        Then only cases with that assigned user are returned
        """
        case_assignment = CaseAssignment.objects.create(
            queue=self.queue, case=self.application_cases[0], user=self.gov_user
        )
        url = f'{reverse("cases:search")}?assigned_user={self.gov_user.pk}'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.application_cases[0].id))

    def test_get_cases_filter_by_assigned_user_with_queue(self):
        case_assignment = CaseAssignment.objects.create(
            queue=self.queue, case=self.application_cases[0], user=self.gov_user
        )
        url = f'{reverse("cases:search")}?assigned_user={self.gov_user.pk}&queue_id={self.queue.id}'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.application_cases[0].id))

    def test_get_cases_filter_by_assigned_user_with_all_cases_queue(self):
        case_assignment = CaseAssignment.objects.create(
            queue=self.queue, case=self.application_cases[0], user=self.gov_user
        )
        url = f'{reverse("cases:search")}?assigned_user={self.gov_user.pk}&queue_id={ALL_CASES_QUEUE_ID}'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.application_cases[0].id))

    def test_get_cases_filter_by_assigned_user_with_queue_no_match(self):
        queue = QueueFactory()
        case_assignment = CaseAssignment.objects.create(queue=queue, case=self.application_cases[0], user=self.gov_user)
        url = f'{reverse("cases:search")}?assigned_user={self.gov_user.pk}&queue_id={self.queue.id}'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    def test_get_cases_filter_by_assigned_user_not_assigned(self):
        """
        Given multiple cases exist with users assigned and not assigned
        When a user requests to view All Cases which have no assigned users
        Then only cases with no assigned users are returned
        """
        all_cases = self.application_cases + self.clc_cases
        case_assignment = CaseAssignment.objects.create(
            queue=self.queue, case=self.application_cases[0], user=self.gov_user
        )
        url = f'{reverse("cases:search")}?assigned_user=not_assigned'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(all_cases) - 1)
        assigned_case = str(self.application_cases[0].id)
        cases_returned = [x["id"] for x in response_data]
        self.assertNotIn(assigned_case, cases_returned)

    def test_get_cases_filter_by_assigned_user_not_assigned_with_queue(self):
        all_cases = self.application_cases + self.clc_cases
        case_assignment = CaseAssignment.objects.create(
            queue=self.queue, case=self.application_cases[0], user=self.gov_user
        )
        url = f'{reverse("cases:search")}?assigned_user=not_assigned&queue_id={self.queue.id}'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(all_cases) - 1)
        assigned_case = str(self.application_cases[0].id)
        cases_returned = [x["id"] for x in response_data]
        self.assertNotIn(assigned_case, cases_returned)

    def test_get_cases_filter_by_assigned_user_not_assigned_with_queue_match(self):
        all_cases = self.application_cases + self.clc_cases
        queue = QueueFactory()
        case_assignment = CaseAssignment.objects.create(queue=queue, case=self.application_cases[0], user=self.gov_user)
        url = f'{reverse("cases:search")}?assigned_user=not_assigned&queue_id={self.queue.id}'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unassigned_case = str(self.application_cases[0].id)
        cases_returned = [x["id"] for x in response_data]
        self.assertIn(unassigned_case, cases_returned)

    def test_get_submitted_status_and_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view Cases of type 'CLC query'
        Then only Cases of that type are returned
        """
        case_status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        clc_submitted_cases = list(filter(lambda case: case.status == case_status, self.clc_cases))
        url = f"{self.url}?case_type={CaseTypeEnum.GOODS.reference}&status={case_status.status}"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clc_submitted_cases), len(response_data["cases"]))
        # Assert Case Type
        for case in response_data["cases"]:
            case_type_reference = Case.objects.filter(pk=case["id"]).values_list("case_type__reference", flat=True)[0]
            self.assertEqual(case_type_reference, CaseTypeEnum.GOODS.reference)

    def test_tab_all_cases_search(self):
        """
        Given there is a case with an ECJU Query that has not been responded to
        When the tab is 'all_cases' and a team queue is not chosen
        Then all cases are returned
        """
        all_cases = self.application_cases + self.clc_cases

        ## create an open ecju query that should be returned
        case_with_open_query = self.application_cases[0]
        self.create_ecju_query(case_with_open_query, gov_user=self.gov_user)

        url = f"{self.url}?selected_tab=all_cases"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(len(response_data), len(all_cases))
        cases_returned = [x["id"] for x in response_data]
        self.assertIn(str(case_with_open_query.id), cases_returned)

    def test_tab_open_queries_cases_search(self):
        """
        Given there is a case with an ECJU Query that has not been responded to
        When a user requests the open queries tab
        Then only cases with open queries are returned
        """
        ## create an ecju query for a case that should appear in tab
        case_with_open_query = self.application_cases[0]
        self.create_ecju_query(case_with_open_query, gov_user=self.gov_user)

        ## create an ecju query with a response so it should not appear in tab
        ecju_query_with_response = EcjuQuery(
            question="ECJU Query 2",
            case=self.application_cases[1],
            response="I have a response",
            raised_by_user=self.gov_user,
            responded_by_user=self.exporter_user,
            query_type=PicklistType.ECJU,
        )
        ecju_query_with_response.save()
        url = f"{self.url}?selected_tab=open_queries"

        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response_data["count"], 1)
        self.assertEqual(response_data["results"]["cases"][0]["id"], str(case_with_open_query.id))

    def test_tab_my_cases_search(self):
        """
        Given there is a case that I am assigned to
        And there is a case where I am a case officer
        When the  user requests the 'my_cases' tab
        Then those two cases are returned
        """
        ## create a case where I am case officer
        case_officer_case = self.application_cases[0]
        case_officer_case.case_officer = self.gov_user
        case_officer_case.save()

        ## create a case assigned to me
        user_assigned_case = self.application_cases[1]
        CaseAssignment.objects.create(queue=self.queue, case=user_assigned_case, user=self.gov_user)

        url = f"{self.url}?selected_tab=my_cases"

        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()["results"]["cases"]

        self.assertEqual(len(response_data), 2)
        cases_returned = [x["id"] for x in response_data]
        self.assertIn(str(user_assigned_case.id), cases_returned)
        self.assertIn(str(case_officer_case.id), cases_returned)

    def test_head_request(self):
        """
        Given there is are cases
        When a HEAD request is sent to view cases with no params
        Then the count for all cases is returned in the header
        """
        all_cases = self.application_cases + self.clc_cases

        response = self.client.head(self.url, **self.gov_headers)

        response_headers = response.headers

        self.assertEqual(response_headers["Resource-Count"], f"{len(all_cases)}")

    def test_head_request_open_queries_tab(self):
        """
        Given there is a case with an ECJU Query that has not been responded to
        When a HEAD request is sent to view cases with open queries
        Then the count for open queries is returned in the header
        """

        ## create an ecju query for a case that should appear in tab
        case_with_open_query = self.application_cases[0]
        self.create_ecju_query(case_with_open_query, gov_user=self.gov_user)

        ## create an ecju query with a response so it should not appear in count
        ecju_query_with_response = EcjuQuery(
            question="ECJU Query 2",
            case=self.application_cases[1],
            response="I have a response",
            raised_by_user=self.gov_user,
            responded_by_user=self.exporter_user,
            query_type=PicklistType.ECJU,
        )
        ecju_query_with_response.save()
        url = f"{self.url}?selected_tab=open_queries"

        response = self.client.head(url, **self.gov_headers)

        response_headers = response.headers

        self.assertEqual(response_headers["Resource-Count"], "1")

    def test_head_request_my_cases_tab(self):
        """
        Given there is a case assigned to me
        And a case where I am assigned as case officer
        When a HEAD request is sent with 'my_cases' as selected tab
        Then header returns a count of 2
        """

        ## create a case where I am case officer
        case_officer_case = self.application_cases[0]
        case_officer_case.case_officer = self.gov_user
        case_officer_case.save()

        ## create a case assigned to me
        user_assigned_case = self.application_cases[1]
        CaseAssignment.objects.create(queue=self.queue, case=user_assigned_case, user=self.gov_user)

        url = f"{self.url}?selected_tab=my_cases"

        response = self.client.head(url, **self.gov_headers)
        response_headers = response.headers

        self.assertEqual(response_headers["Resource-Count"], "2")

    @parameterized.expand(
        [
            [FlagsEnum.SMALL_ARMS, "goods_flags"],
            [FlagsEnum.LU_COUNTER_REQUIRED, "destinations_flags"],
        ]
    )
    def test_filter_cases_by_flags(self, flag_id, flags_key):

        # set required flags
        for application in self.application_cases:
            case = Case.objects.get(id=application.id)

            good_on_application = application.goods.first()
            good_on_application.good.flags.add(Flag.objects.get(id=FlagsEnum.SMALL_ARMS))

            party_on_application = application.parties.first()
            party_on_application.party.flags.add(Flag.objects.get(id=FlagsEnum.LU_COUNTER_REQUIRED))

        url = f"{self.url}?flags={flag_id}"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.application_cases), len(response_data["cases"]))

        for case in response_data["cases"]:
            self.assertIn(flag_id, [item["id"] for item in case[flags_key]])

    @parameterized.expand(["permanent", "temporary"])
    def test_get_cases_filter_by_export_type(self, export_type):
        expected_id = str(self.application_cases[0].id)
        standard_app = self.application_cases[0].baseapplication.standardapplication
        standard_app.export_type = export_type
        standard_app.save()
        url = f'{reverse("cases:search")}?export_type={export_type}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]
        all_response_case_ids = [case["id"] for case in response_data]
        self.assertTrue(expected_id in all_response_case_ids)

    def test_get_cases_filter_by_assigned_queues_match(self):
        queue = QueueFactory()
        case = self.application_cases[0]
        case.queues.add(queue)
        url = f'{reverse("cases:search")}?assigned_queues={queue.id}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertTrue(response_data[0]["id"], str(case.id))

    def test_get_cases_filter_by_assigned_queues_no_results(self):
        queue = QueueFactory()
        url = f'{reverse("cases:search")}?assigned_queues={queue.id}'

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    def test_get_cases_filter_by_max_total_value_no_results(self):
        case = self.application_cases[0]
        good = case.baseapplication.goods.first()
        good.value = 200
        good.save()
        url = f'{reverse("cases:search")}?reference_code={case.reference_code}&max_total_value=199'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    def test_get_cases_filter_by_max_total_value_match(self):
        case = self.application_cases[0]
        good = case.baseapplication.goods.first()
        good.value = 200
        good.save()
        url = f'{reverse("cases:search")}?case_reference={case.reference_code}&max_total_value=201'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertTrue(response_data[0]["id"], str(case.id))

    def test_get_cases_filter_by_max_total_value_bad_decimal(self):
        case = self.application_cases[0]
        good = case.baseapplication.goods.first()
        good.value = 200
        good.save()
        url = f'{reverse("cases:search")}?case_reference={case.reference_code}&max_total_value=foo'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertTrue(response_data[0]["id"], str(case.id))

    def test_get_cases_filter_by_goods_starting_point_not_in_case(self):
        url = f'{reverse("cases:search")}?goods_starting_point=NI'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 0)

    @parameterized.expand(["NI", "GB"])
    def test_get_cases_filter_by_goods_starting_point_present_on_application(self, starting_point):
        application = self.application_cases[0]
        application.goods_starting_point = starting_point
        application.save()
        case = Case.objects.get(id=application.id)

        url = f'{reverse("cases:search")}?goods_starting_point={starting_point}&case_reference={case.reference_code}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertTrue(response_data[0]["id"], str(application.id))

    def test_get_cases_filter_exclude_denial_matches_no_denial_match_cases(self):
        application = self.application_cases[0]
        case = Case.objects.get(id=application.id)
        url = f'{reverse("cases:search")}?exclude_denial_matches=True&case_reference={case.reference_code}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertTrue(response_data[0]["id"], str(application.id))

    def test_get_cases_filter_exclude_denial_matches_denial_match_excluded(self):

        application = self.application_cases[0]
        denial = DenialMatchFactory()
        denial_on_application = DenialMatchOnApplicationFactory(
            application=application, category="exact", denial=denial
        )
        case = Case.objects.get(id=application.id)
        url = f'{reverse("cases:search")}?exclude_denial_matches=True&case_reference={case.reference_code}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    def test_get_cases_filter_exclude_sanction_matches_no_sanction_match_cases(self):
        application = self.application_cases[0]
        case = Case.objects.get(id=application.id)
        url = f'{reverse("cases:search")}?exclude_sanction_matches=True&case_reference={case.reference_code}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertTrue(response_data[0]["id"], str(application.id))

    def test_get_cases_filter_exclude_sanction_matches_sanction_match_excluded(self):

        application = self.application_cases[0]
        sanction_match = SanctionMatchFactory(
            party_on_application=application.parties.first(), flag_uuid=Flag.objects.first().id, is_revoked=False
        )
        case = Case.objects.get(id=application.id)
        url = f'{reverse("cases:search")}?exclude_sanction_matches=True&case_reference={case.reference_code}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    @parameterized.expand(
        [
            (["NI", "GB"], []),
            (["NI", "GB"], ["GB"]),
            (["NI", "GB"], ["NI"]),
            (["NI", "GB"], ["NI", "GB"]),
            (["NI", "GB"], ["NI", "GB", "US"]),
        ]
    )
    def test_get_cases_filter_by_countries_match(self, countries_on_application, filter_countries):
        application = self.application_cases[0]
        for country in countries_on_application:
            PartyOnApplicationFactory(application=application, party__country_id=country)
        case = Case.objects.get(id=application.id)

        params = [f"case_reference={case.reference_code}"]
        for country in filter_countries:
            params.append(f"countries={country}")
        params_raw = "&".join(params)

        url = f'{reverse("cases:search")}?{params_raw}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertTrue(response_data[0]["id"], str(application.id))

    @parameterized.expand(
        [
            (["NI", "GB"], ["US"]),
            (["NI", "GB"], ["US", "FR"]),
        ]
    )
    def test_get_cases_filter_by_countries_no_match(self, countries_on_application, filter_countries):
        application = self.application_cases[0]
        for country in countries_on_application:
            PartyOnApplicationFactory(application=application, party__country_id=country)
        case = Case.objects.get(id=application.id)

        params = [f"case_reference={case.reference_code}"]
        for country in filter_countries:
            params.append(f"countries={country}")
        params_raw = "&".join(params)

        url = f'{reverse("cases:search")}?{params_raw}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    @parameterized.expand(
        [
            (["NI", "GB"], ""),
            (["NI", "GB"], "GB"),
            (["NI", "GB"], "NI"),
        ]
    )
    def test_get_cases_filter_by_country_match(self, countries_on_application, filter_country):
        application = self.application_cases[0]
        for country in countries_on_application:
            PartyOnApplicationFactory(application=application, party__country_id=country)
        case = Case.objects.get(id=application.id)

        url = f'{reverse("cases:search")}?case_reference={case.reference_code}&country={filter_country}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertTrue(response_data[0]["id"], str(application.id))

    @parameterized.expand(
        [
            (["NI", "GB"], "US"),
            (["NI", "GB"], "FR"),
        ]
    )
    def test_get_cases_filter_by_country_no_match(self, countries_on_application, filter_country):
        application = self.application_cases[0]
        for country in countries_on_application:
            PartyOnApplicationFactory(application=application, party__country_id=country)
        case = Case.objects.get(id=application.id)

        url = f'{reverse("cases:search")}?case_reference={case.reference_code}&country={filter_country}"'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)


class UpdatedCasesQueueTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.case = self.create_standard_application_case(self.organisation).get_case()
        self.old_status = self.case.status.status
        self.case.queues.set([self.queue])
        self.case_assignment = CaseAssignment.objects.create(case=self.case, queue=self.queue, user=self.gov_user)
        self.case.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.case.save()

        self.audit = Audit.objects.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_STATUS,
            target=self.case,
            payload={"status": {"new": CaseStatusEnum.APPLICANT_EDITING, "old": self.old_status}},
        )
        self.gov_user.send_notification(content_object=self.audit, case=self.case)

        self.url = f'{reverse("cases:search")}?queue_id={UPDATED_CASES_QUEUE_ID}'

    def test_get_cases_on_updated_cases_queue_when_user_is_assigned_to_a_case_returns_expected_cases(self):
        # Create another case that does not have an update
        case = self.create_standard_application_case(self.organisation).get_case()
        case.queues.set([self.queue])
        case_assignment = CaseAssignment.objects.create(case=case, queue=self.queue, user=self.gov_user)
        self.gov_user.send_notification(content_object=self.audit, case=case)

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 2)  # Count is 2 as another case is created in setup
        self.assertEqual(response_data[0]["id"], str(self.case.id))

    def test_get_cases_on_updated_cases_queue_non_team_queue(self):
        other_team = self.create_team("other_team")
        self.gov_user.team = other_team

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.case.id))

    def test_get_cases_on_updated_cases_queue_when_user_is_not_assigned_to_a_case_returns_no_cases(self):
        other_user = GovUserFactory(
            baseuser_ptr__email="test2@mail.com",
            baseuser_ptr__first_name="John",
            baseuser_ptr__last_name="Smith",
            team=self.team,
        )
        gov_headers = {"HTTP_GOV_USER_TOKEN": user_to_token(other_user.baseuser_ptr)}

        response = self.client.get(self.url, **gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 0)

    def test_get_cases_on_updated_cases_queue_when_user_is_assigned_as_case_officer_returns_expected_cases(self):
        CaseAssignment.objects.filter(case=self.case, queue=self.queue).delete()
        self.case.case_officer = self.gov_user
        self.case.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.case.id))

    def test_get_cases_on_updated_cases_queue_when_user_is_assigned_to_case_and_as_case_officer_returns_expected_cases(
        self,
    ):
        self.case.case_officer = self.gov_user
        self.case.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.case.id))


class CaseOrderingOnQueueTests(DataTestClient):
    def test_all_cases_queue_returns_cases_in_expected_order(self):
        """Test All cases queue returns cases in expected order (newest first)."""
        url = reverse("cases:search")
        clc_query = self.create_clc_query("Example CLC Query", self.organisation)
        standard_app = self.create_standard_application_case(self.organisation, "Example Application")
        clc_query_2 = self.create_clc_query("Example CLC Query 2", self.organisation)

        QueueFactory(team=self.gov_user.team, cases=[clc_query, standard_app, clc_query_2])

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        actual_case_order_ids = [case["id"] for case in response.json()["results"]["cases"]]
        expected_case_order_ids = [str(clc_query_2.id), str(standard_app.id), str(clc_query.id)]
        self.assertEqual(actual_case_order_ids, expected_case_order_ids)

    def test_work_queue_returns_cases_in_expected_order(self):
        """Test that a work queue returns cases in expected order (hmrc queries with goods not departed first)."""
        clc_query_1 = self.create_clc_query("Example CLC Query", self.organisation)
        standard_app = self.create_standard_application_case(self.organisation, "Example Application")
        hmrc_query_1 = self.submit_application(self.create_hmrc_query(self.organisation))
        clc_query_2 = self.create_clc_query("Example CLC Query 2", self.organisation)
        hmrc_query_2 = self.submit_application(self.create_hmrc_query(self.organisation, have_goods_departed=True))

        queue = QueueFactory(
            team=self.gov_user.team, cases=[clc_query_1, standard_app, hmrc_query_1, clc_query_2, hmrc_query_2]
        )

        url = reverse("cases:search") + "?queue_id=" + str(queue.id)
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        actual_case_order_ids = [case["id"] for case in response.json()["results"]["cases"]]
        expected_case_order_ids = [
            str(hmrc_query_1.id),
            str(clc_query_1.id),
            str(standard_app.id),
            str(clc_query_2.id),
            str(hmrc_query_2.id),
        ]
        self.assertEqual(actual_case_order_ids, expected_case_order_ids)


class OpenEcjuQueriesForTeamOnWorkQueueTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.other_team = self.create_team("other team")
        self.other_team_gov_user = self.create_gov_user("new_user@digital.trade.gov.uk", self.other_team)
        self.queue = self.create_queue("my new queue", self.team)
        self.case = self.create_standard_application_case(self.organisation)
        self.case.queues.set([self.queue])
        self.url = reverse("cases:search") + "?queue_id=" + str(self.queue.id)

    def test_get_case_from_queue(self):
        response = self.client.get(self.url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response_data["count"], 1)
        self.assertEqual(response_data["results"]["queue"]["id"], str(self.queue.id))
        self.assertEqual(response_data["results"]["cases"][0]["id"], str(self.case.id))

    def test_do_not_get_case_with_open_team_ecju(self):
        self.create_ecju_query(self.case, gov_user=self.gov_user)
        response = self.client.get(self.url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response_data["count"], 0)

    def test_get_case_with_only_closed_team_ecju(self):
        ecju_query = self.create_ecju_query(self.case, gov_user=self.gov_user)
        ecju_query.response = "response"
        ecju_query.responded_at = datetime.datetime.now()
        ecju_query.responded_by_user = self.exporter_user
        ecju_query.save()

        response = self.client.get(self.url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response_data["count"], 1)

    def test_get_case_with_other_team_open_ecju(self):
        self.create_ecju_query(self.case, gov_user=self.other_team_gov_user)
        response = self.client.get(self.url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response_data["count"], 1)


class SearchAPITest(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("cases:search")

    def _create_data(self):
        self.application = StandardApplicationFactory(case_type=CaseType.objects.get(reference="siel"))
        self.case = Case.objects.get(id=self.application.id)
        self.case.submitted_at = django_utils.timezone.now()
        self.case.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        self.case.save()
        self.queue.cases.add(self.case)
        self.queue.save()
        self.assignment = CaseAssignment(user=self.gov_user, case=self.case, queue=self.queue)
        self.assignment.save()
        self.denial = DenialMatchFactory()
        self.denial_on_application = DenialMatchOnApplicationFactory(
            application=self.application, category="exact", denial=self.denial
        )
        prefix = ReportSummaryPrefixFactory()
        subject = ReportSummarySubjectFactory()
        self.good = GoodFactory(organisation=self.case.organisation)
        self.good_on_application = GoodOnApplicationFactory(
            application=self.application,
            good=self.good,
            is_good_controlled=True,
            quantity=10,
            value=20,
            report_summary_subject=subject,
            report_summary_prefix=prefix,
        )
        self.good_on_application.control_list_entries.add(ControlListEntry.objects.first())
        self.good_on_application.regime_entries.add(RegimeEntry.objects.first())
        self.ecju_query = EcjuQuery(
            question="ECJU Query 2",
            case=self.case,
            response="I have a response",
            raised_by_user=self.gov_user,
            responded_by_user=self.exporter_user,
            query_type=PicklistType.ECJU,
            responded_at=datetime.datetime.now(),
        )
        self.ecju_query.save()
        self.advice = self.create_advice(
            self.gov_user, self.case, "good", AdviceType.REFUSE, AdviceLevel.FINAL, good=self.good
        )
        self.create_advice(self.gov_user, self.case, "good", AdviceType.REFUSE, AdviceLevel.FINAL, good=self.good)

    def test_api_success(self):
        self._create_data()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        case_api_result = response_data["cases"][0]
        expected_assignments = {
            str(self.gov_user.pk): {
                "email": self.gov_user.email,
                "first_name": self.gov_user.first_name,
                "last_name": self.gov_user.last_name,
                "queues": [{"id": str(self.queue.id), "name": self.queue.name}],
                "team_id": str(self.gov_user.team.id),
                "team_name": self.gov_user.team.name,
            }
        }
        self.assertEqual(case_api_result["assignments"], expected_assignments)
        self.assertEqual(case_api_result["case_officer"], None)
        self.assertEqual(case_api_result["case_type"]["reference"]["key"], "siel")
        self.assertEqual(case_api_result["destinations"], [])
        self.assertEqual(case_api_result["destinations_flags"], [])
        self.assertEqual(case_api_result["flags"], [])
        self.assertEqual(case_api_result["goods_flags"], [])
        self.assertEqual(case_api_result["has_open_queries"], False)
        self.assertEqual(case_api_result["id"], str(self.case.id))
        self.assertEqual(case_api_result["is_recently_updated"], True)
        self.assertEqual(case_api_result["next_review_date"], None)
        self.assertEqual(case_api_result["organisation"]["name"], self.case.organisation.name)
        self.assertEqual(
            case_api_result["denials"],
            [
                {
                    "name": self.denial.name,
                    "reference": self.denial.reference,
                    "category": self.denial_on_application.category,
                    "address": self.denial.address,
                }
            ],
        )
        self.assertEqual(
            case_api_result["ecju_queries"],
            [
                {
                    "question": self.ecju_query.question,
                    "response": self.ecju_query.response,
                    "raised_by_user": f"{self.ecju_query.raised_by_user.first_name} {self.ecju_query.raised_by_user.last_name}",
                    "responded_by_user": f"{self.ecju_query.responded_by_user.first_name} {self.ecju_query.responded_by_user.last_name}",
                    "query_type": self.ecju_query.query_type,
                }
            ],
        )
        self.assertEqual(
            case_api_result["goods"],
            [
                {
                    "name": self.good_on_application.name,
                    "cles": [self.good_on_application.control_list_entries.all()[0].rating],
                    "report_summary_subject": self.good_on_application.report_summary_subject.name,
                    "report_summary_prefix": self.good_on_application.report_summary_prefix.name,
                    "quantity": "10.00",
                    "value": "20.00",
                    "regimes": [self.good_on_application.regime_entries.all()[0].name],
                }
            ],
        )
        self.assertEqual(case_api_result["intended_end_use"], self.application.intended_end_use)
        expected_queues = [
            {
                "countersigning_queue": self.queue.countersigning_queue,
                "id": str(self.queue.id),
                "name": self.queue.name,
                "team": {
                    "alias": self.queue.team.alias,
                    "id": str(self.queue.team.id),
                    "is_ogd": self.queue.team.is_ogd,
                    "name": self.queue.team.name,
                    "part_of_ecju": self.queue.team.part_of_ecju,
                },
            }
        ]
        self.assertEqual(case_api_result["queues"], expected_queues)
        self.assertEqual(case_api_result["reference_code"], self.case.reference_code)
        self.assertEqual(case_api_result["sla_days"], 0)
        self.assertEqual(case_api_result["sla_remaining_days"], None)
        self.assertEqual(case_api_result["status"]["key"], self.case.status.status)
        self.assertEqual(len(case_api_result["advice"][str(self.advice.user.team.id) + self.advice.type]), 1)

        # Reflect rest framework's way of rendering datetime objects... https://github.com/encode/django-rest-framework/blob/c9e7b68a4c1db1ac60e962053380acda549609f3/rest_framework/utils/encoders.py#L29
        expected_submitted_at = self.case.submitted_at.isoformat()
        if expected_submitted_at.endswith("+00:00"):
            expected_submitted_at = expected_submitted_at[:-6] + "Z"
        self.assertEqual(case_api_result["submitted_at"], expected_submitted_at)
