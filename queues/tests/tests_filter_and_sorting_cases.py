from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from applications.enums import ApplicationStatus
from clc_queries.enums import ClcQueryStatus
from cases.models import Case, CaseAssignment


class CasesFilterAndSortTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.application_cases = []
        self.clc_cases = []
        for application_status in ApplicationStatus.choices:
            case = self.create_application_case('Example Application')
            case.application.status = application_status
            case.save()
            self.queue.cases.add(case)
            self.queue.save()
            case_assignment = CaseAssignment(case=case, queue=self.queue)
            case_assignment.save()
            self.gov_user.case_assignments.add(case_assignment)
            self.application_cases.append(case)

        for clc_query_status in ClcQueryStatus.choices:
            case = self.create_clc_query_case('Example CLC Query', clc_query_status)
            self.queue.cases.add(case)
            self.queue.save()
            case_assignment = CaseAssignment(case=case, queue=self.queue)
            case_assignment.save()
            self.gov_user.case_assignments.add(case_assignment)
            self.clc_cases.append(case)

        self.url = reverse('queues:case_assignment', kwargs={'pk': self.queue.pk})

    def test_get_cases_no_filter(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases with no filter
        Then all Cases are returned
        """

        # Arrange

        # Act
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()['case_assignments']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.application_cases) + len(self.clc_cases), len(response_data))

    def test_get_application_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'application'
        Then only Cases with that type are returned
        """

        # Arrange

        # Act
        response = self.client.get(self.url + '?case_type=application', **self.gov_headers)
        response_data = response.json()['case_assignments']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.application_cases))
        for case_assignment in response_data:
            case_type = Case.objects.filter(pk=case_assignment['case']).values_list('case_type__name', flat=True)[0]
            self.assertEqual('Licence application', case_type)
