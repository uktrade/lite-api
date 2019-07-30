from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from applications.enums import ApplicationStatus
from clc_queries.enums import ClcQueryStatus
from cases.models import Case, CaseAssignment


class CasesFilterAndSortTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.url = reverse('queues:case_assignment', kwargs={'pk': self.queue.pk})

        self.application_cases = []
        for app_status in ApplicationStatus.choices:
            case = self.create_application_case('Example Application')
            case.application.status = app_status
            case.application.save(update_fields=['status'])
            self.queue.cases.add(case)
            self.queue.save()
            case_assignment = CaseAssignment(case=case, queue=self.queue)
            case_assignment.save()
            self.gov_user.case_assignments.add(case_assignment)
            self.application_cases.append(case)

        self.clc_cases = []
        for clc_status in ClcQueryStatus.choices:
            case = self.create_clc_query_case('Example CLC Query', clc_status)
            self.queue.cases.add(case)
            self.queue.save()
            case_assignment = CaseAssignment(case=case, queue=self.queue)
            case_assignment.save()
            self.gov_user.case_assignments.add(case_assignment)
            self.clc_cases.append(case)

        return

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
        response_data = response.json()['case_assignments']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_cases), len(response_data))

    def test_get_app_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'Licence application'
        Then only Cases of that type are returned
        """

        # Arrange
        url = self.url + '?filters={"case_type":"Licence%20application"}'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['case_assignments']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.application_cases))
        # Assert Case Type
        for case_assignment in response_data:
            case_type = Case.objects.filter(pk=case_assignment['case']).values_list('case_type__name', flat=True)[0]
            self.assertEqual('Licence application', case_type)

    def test_get_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        url = self.url + '?filters={"case_type":"CLC%20query"}'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['case_assignments']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.clc_cases))
        # Assert Case Type
        for case_assignment in response_data:
            case_type = Case.objects.filter(pk=case_assignment['case']).values_list('case_type__name', flat=True)[0]
            self.assertEqual('CLC query', case_type)

    def test_get_submitted_status_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        url = self.url + '?filters={"case_type":"CLC%20query"}'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['case_assignments']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.clc_cases))
        # Assert Case Type
        for case_assignment in response_data:
            case_type = Case.objects.filter(pk=case_assignment['case']).values_list('case_type__name', flat=True)[0]
            self.assertEqual('CLC query', case_type)

    def test_get_submitted_status_and_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        case_status = 'submitted'
        clc_submitted_cases = list(filter(
            lambda case: case.clc_query.status == (case_status, case_status.capitalize()),
            self.clc_cases
        ))
        url = self.url + '?filters={"case_type":"CLC%20query", "status":"' + case_status + '"}'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['case_assignments']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(clc_submitted_cases))
        # Assert Case Type
        for case_assignment in response_data:
            case_type = Case.objects.filter(pk=case_assignment['case']).values_list('case_type__name', flat=True)[0]
            self.assertEqual('CLC query', case_type)

    def test_get_cases_no_filter_sort_by_status(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases sorted by case_type
        Then all Cases are sorted and returned
        """

        # Arrange
        all_cases = self.application_cases + self.clc_cases
        all_cases = [{'case': str(case.id),
                      'status': case.application.status[0] if case.application is not None else case.clc_query.status[0]
                      } for case in all_cases]
        all_cases_sorted = sorted(all_cases, key=lambda k: k['status'])
        url = self.url + '?sort=status'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['case_assignments']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_cases), len(response_data))
        # Assert ordering
        for i in range(0, len(response_data)):
            self.assertEqual(response_data[i]['case'], all_cases_sorted[i]['case'])

    def test_get_app_type_cases_sorted_by_status(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases sorted by case_type
        Then all Cases are sorted and returned
        """

        # Arrange
        application_cases_sorted = sorted(
            [{'case': str(case.id), 'status': case.application.status[0]} for case in self.application_cases],
            key=lambda k: k['status']
        )
        url = self.url + '?filters={"case_type":"Licence%20application"}&sort=status'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['case_assignments']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.application_cases), len(response_data))
        for i in range(0, len(response_data)):
            # Assert Case Type
            case_type = Case.objects.filter(pk=response_data[i]['case']).values_list('case_type__name', flat=True)[0]
            self.assertEqual('Licence application', case_type)
            # Assert ordering
            self.assertEqual(response_data[i]['case'], application_cases_sorted[i]['case'])
