from django.test import tag
from django.urls import reverse
from rest_framework import status

from audit_trail.models import Audit
from audit_trail.payload import AuditType
from cases.models import Case, CaseAssignment
from queues.constants import (
    UPDATED_CASES_QUEUE_ID,
    MY_ASSIGNED_CASES_QUEUE_ID,
    MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
)
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token
from users.models import GovUser


class FilterAndSortTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("cases:search")

        self.application_cases = []
        for app_status in CaseStatusEnum.choices:
            case = self.create_standard_application_case(self.organisation, "Example Application")
            case.status = get_case_status_by_status(app_status[0])
            case.save()
            self.queue.cases.add(case)
            self.queue.save()
            self.application_cases.append(case)

        # CLC applicable case statuses
        clc_statuses = [CaseStatusEnum.SUBMITTED, CaseStatusEnum.CLOSED, CaseStatusEnum.WITHDRAWN]
        self.clc_cases = []
        for clc_status in clc_statuses:
            clc_query = self.create_clc_query("Example CLC Query", self.organisation)
            clc_query.status = get_case_status_by_status(clc_status)
            clc_query.save()
            self.queue.cases.add(clc_query)
            self.queue.save()
            self.clc_cases.append(clc_query)

    def test_get_cases_no_filter(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases with no filter
        Then all Cases are returned
        """

        # Arrange
        all_cases = self.application_cases + self.clc_cases

        # Act
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_cases), len(response_data["cases"]))

    def test_get_app_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'Licence application'
        Then only Cases of that type are returned
        """

        # Arrange
        url = self.url + "?case_type=application"

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.application_cases), len(response_data["cases"]))
        # Assert Case Type
        for case in response_data["cases"]:
            case_type = Case.objects.filter(pk=case["id"]).values_list("type", flat=True)[0]
            self.assertEqual(case_type, "application")

    def test_get_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        url = self.url + "?case_type=clc_query"

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.clc_cases), len(response_data["cases"]))

        # Assert Case Type
        for case in response_data["cases"]:
            case_type = Case.objects.filter(pk=case["id"]).values_list("type", flat=True)[0]
            self.assertEqual(case_type, "clc_query")

    def test_get_submitted_status_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        url = self.url + "?case_type=clc_query"

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.clc_cases), len(response_data["cases"]))
        # Assert Case Type
        for case in response_data["cases"]:
            case_type = Case.objects.filter(pk=case["id"]).values_list("type", flat=True)[0]
            self.assertEqual(case_type, "clc_query")

    def test_get_all_cases_queue_submitted_status_and_clc_type_cases(self):
        """
        Given multiple cases exist with different statuses and case-types
        When a user requests to view All Cases of type 'CLC query'
        Then only cases of that type are returned
        """

        # Arrange
        case_status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        clc_submitted_cases = list(filter(lambda c: c.query.status == case_status, self.clc_cases))
        url = f'{reverse("cases:search")}?case_type=clc_query&status={case_status.status}&sort=status'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clc_submitted_cases), len(response_data["cases"]))
        # Assert Case Type
        for case in response_data["cases"]:
            case_type = Case.objects.filter(pk=case["id"]).values_list("type", flat=True)[0]
            self.assertEqual("clc_query", case_type)

    @tag("only")
    def test_get_cases_filter_by_case_officer(self):
        """
        Given multiple cases exist with case officers attached and not attached
        When a user requests to view All Cases when the case officer is set to themselves
        Then only cases of that type are returned
        """

        # Arrange
        self.application_cases[0].case_officer = self.gov_user
        self.application_cases[0].save()
        url = f'{reverse("cases:search")}?case_officer=' + str(self.gov_user.id)

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)

    @tag("only")
    def test_get_cases_filter_by_case_officer_not_assigned(self):
        """
        Given multiple cases exist with case officers attached and not attached
        When a user requests to view All Cases when the case officer is set to not_assigned
        Then only cases with no assigned case officers are returned
        """

        # Arrange
        all_cases = self.application_cases + self.clc_cases
        self.application_cases[0].case_officer = self.gov_user
        self.application_cases[0].save()
        url = f'{reverse("cases:search")}?case_officer=not_assigned'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(all_cases) - 1)

    @tag("only")
    def test_get_cases_filter_by_assigned_user(self):
        """
        Given multiple cases exist with users assigned and not assigned
        When a user requests to view All Cases when the assigned user is set to themselves
        Then only cases with that assigned user are returned
        """

        # Arrange
        case_assignment = CaseAssignment(queue=self.queue, case=self.application_cases[0])
        case_assignment.users.set([self.gov_user])
        case_assignment.save()
        url = f'{reverse("cases:search")}?assigned_user=' + str(self.gov_user.id)

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)

    @tag("only")
    def test_get_cases_filter_by_assigned_user_not_assigned(self):
        """
        Given multiple cases exist with users assigned and not assigned
        When a user requests to view All Cases when the assigned user is set to themselves
        Then only cases with that assigned user are returned
        """

        # Arrange
        all_cases = self.application_cases + self.clc_cases
        case_assignment = CaseAssignment(queue=self.queue, case=self.application_cases[0])
        case_assignment.users.set([self.gov_user])
        case_assignment.save()
        url = f'{reverse("cases:search")}?assigned_user=not_assigned'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]["cases"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(all_cases) - 1)

    def test_get_submitted_status_and_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        case_status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        clc_submitted_cases = list(filter(lambda case: case.status == case_status, self.clc_cases))
        url = self.url + "?case_type=clc_query&status=" + case_status.status

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clc_submitted_cases), len(response_data["cases"]))
        # Assert Case Type
        for case in response_data["cases"]:
            case_type = Case.objects.filter(pk=case["id"]).values_list("type", flat=True)[0]
            self.assertEqual(case_type, "clc_query")

    def test_get_cases_no_filter_sort_by_status_ascending(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases sorted by case_type
        Then all Cases are sorted in ascending order and returned
        """

        # Arrange
        all_cases = self.application_cases + self.clc_cases
        all_cases = [{"status": case.status.status, "status_ordering": case.status.priority,} for case in all_cases]
        all_cases_sorted = sorted(all_cases, key=lambda k: k["status_ordering"])
        url = self.url + "?sort=status"

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_cases), len(response_data["cases"]))

        # Assert ordering
        for case, expected_case in zip(response_data["cases"], all_cases_sorted):
            self.assertEqual(case["status"], expected_case["status"])

    def test_get_app_type_cases_sorted_by_status_descending(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases sorted by case_type
        Then all Cases are sorted in descending order and returned
        """

        # Arrange
        application_cases_sorted = sorted(
            [
                {"status": case.status.status, "status_ordering": case.status.priority, "id": str(case.id),}
                for case in self.application_cases
            ],
            key=lambda k: k["status_ordering"],
            reverse=True,
        )

        url = self.url + "?case_type=application&sort=-status"

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.application_cases), len(response_data["cases"]))
        for case, expected_case in zip(response_data["cases"], application_cases_sorted):
            # Assert Case Type
            case_type = Case.objects.filter(pk=case["id"]).values_list("type", flat=True)[0]
            self.assertEqual(case_type, "application")
            # Assert ordering
            self.assertEqual(case["status"], expected_case["status"])
            self.assertEqual(case["id"], expected_case["id"])


class FilterQueueUpdatedCasesTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.case = self.create_standard_application_case(self.organisation).get_case()
        self.case.queues.set([self.queue])
        self.case_assignment = CaseAssignment.objects.create(case=self.case, queue=self.queue)
        self.case_assignment.users.set([self.gov_user])
        self.case.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.case.save()

        self.audit = Audit.objects.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_STATUS.value,
            target=self.case,
            payload={"status": CaseStatusEnum.APPLICANT_EDITING},
        )
        self.gov_user.send_notification(content_object=self.audit, case=self.case)

        self.url = reverse("cases:search") + "?queue_id=" + UPDATED_CASES_QUEUE_ID

    def test_get_cases_on_updated_cases_queue_when_user_is_assigned_to_a_case_returns_expected_cases(self):
        # Create another case that does not have an update
        case = self.create_standard_application_case(self.organisation).get_case()
        case.queues.set([self.queue])
        case_assignment = CaseAssignment.objects.create(case=case, queue=self.queue)
        case_assignment.users.set([self.gov_user])

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 1)  # Count is 1 as another case is created in setup
        self.assertEqual(response_data[0]["id"], str(self.case.id))

    def test_get_cases_on_updated_cases_queue_when_user_is_not_assigned_to_a_case_returns_no_cases(self):
        other_user = GovUser.objects.create(email="test@mail.com", first_name="John", last_name="Smith", team=self.team)
        gov_headers = {"HTTP_GOV_USER_TOKEN": user_to_token(other_user)}

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


class FilterUserAssignedCasesQueueTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.user_assigned_case = self.create_standard_application_case(self.organisation).get_case()
        self.user_assigned_case.queues.set([self.queue])
        self.case_assignment = CaseAssignment.objects.create(case=self.user_assigned_case, queue=self.queue)
        self.case_assignment.users.set([self.gov_user])

        self.url = reverse("cases:search") + "?queue_id=" + MY_ASSIGNED_CASES_QUEUE_ID

    def test_get_cases_on_user_assigned_to_case_queue_returns_expected_cases(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.user_assigned_case.id))

    def test_get_cases_on_user_assigned_to_case_queue_doesnt_return_closed_cases(self):
        user_assigned_case = self.create_standard_application_case(self.organisation).get_case()
        user_assigned_case.queues.set([self.queue])
        case_assignment = CaseAssignment.objects.create(case=self.user_assigned_case, queue=self.queue)
        case_assignment.users.set([self.gov_user])
        user_assigned_case.status = get_case_status_by_status(CaseStatusEnum.WITHDRAWN)
        user_assigned_case.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 1)
        self.assertNotEqual(response_data[0]["id"], str(user_assigned_case.id))


class FilterQueueUserAssignedAsCaseOfficerTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.case_officer_case = self.create_standard_application_case(self.organisation).get_case()
        self.case_officer_case.queues.set([self.queue])
        self.case_officer_case.case_officer = self.gov_user
        self.case_officer_case.save()

        self.url = reverse("cases:search") + "?queue_id=" + MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID

    def test_get_cases_on_user_assigned_as_case_officer_queue_returns_expected_cases(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.case_officer_case.id))

    def test_get_cases_on_user_assigned_as_case_officer_queue_doesnt_return_closed_cases(self):
        case_officer_case = self.create_standard_application_case(self.organisation).get_case()
        case_officer_case.queues.set([self.queue])
        case_officer_case.case_officer = self.gov_user
        case_officer_case.status = get_case_status_by_status(CaseStatusEnum.WITHDRAWN)
        case_officer_case.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertEqual(len(response_data), 1)
        self.assertNotEqual(response_data[0]["id"], str(case_officer_case.id))
