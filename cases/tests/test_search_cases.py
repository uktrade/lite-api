from django.urls import reverse
from rest_framework import status

from cases.models import Case
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status_enum
from test_helpers.clients import DataTestClient


class CasesFilterAndSortTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.url = reverse('cases:search')

        self.application_cases = []
        for app_status in CaseStatusEnum.choices:
            case = self.create_standard_application_case(self.organisation, 'Example Application')
            case.application.status = get_case_status_from_status_enum(app_status)
            case.application.save()
            self.queue.cases.add(case)
            self.queue.save()
            self.application_cases.append(case)

        self.clc_cases = []
        for clc_status in CaseStatusEnum.choices:
            clc_query = self.create_clc_query('Example CLC Query', self.organisation)
            clc_query.status = get_case_status_from_status_enum(clc_status)
            clc_query.save()
            self.queue.cases.add(clc_query.case.get())
            self.queue.save()
            self.clc_cases.append(clc_query.case.get())

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
        response_data = response.json()['data']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_cases), len(response_data['cases']))

    def test_get_app_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'Licence application'
        Then only Cases of that type are returned
        """

        # Arrange
        url = self.url + '?case_type=application'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['data']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.application_cases), len(response_data['cases']))
        # Assert Case Type
        for case in response_data['cases']:
            case_type = Case.objects.filter(pk=case['id']).values_list('type', flat=True)[0]
            self.assertEqual(case_type, 'application')

    def test_get_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        url = self.url + '?case_type=clc_query'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['data']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.clc_cases), len(response_data['cases']))

        # Assert Case Type
        for case in response_data['cases']:
            case_type = Case.objects.filter(pk=case['id']).values_list('type', flat=True)[0]
            self.assertEqual(case_type, 'clc_query')

    def test_get_submitted_status_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        url = self.url + '?case_type=clc_query'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['data']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.clc_cases), len(response_data['cases']))
        # Assert Case Type
        for case in response_data['cases']:
            case_type = Case.objects.filter(pk=case['id']).values_list('type', flat=True)[0]
            self.assertEqual(case_type, 'clc_query')

    def test_get_all_cases_queue_submitted_status_and_clc_type_cases(self):
        """
        Given multiple cases exist with different statuses and case-types
        When a user requests to view All Cases of type 'CLC query'
        Then only cases of that type are returned
        """

        # Arrange
        case_status = get_case_status_from_status_enum(CaseStatusEnum.SUBMITTED)
        clc_submitted_cases = list(filter(lambda c: c.query.status == case_status, self.clc_cases))
        url = f'{reverse("cases:search")}?case_type=clc_query&status={case_status.status}&sort=status'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['data']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clc_submitted_cases), len(response_data['cases']))
        # Assert Case Type
        for case in response_data['cases']:
            case_type = Case.objects.filter(pk=case['id']).values_list('type', flat=True)[0]
            self.assertEqual('clc_query', case_type)

    def test_get_submitted_status_and_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        case_status = get_case_status_from_status_enum(CaseStatusEnum.SUBMITTED)
        clc_submitted_cases = list(filter(lambda case: case.query.status == case_status, self.clc_cases))
        url = self.url + '?case_type=clc_query&status=' + case_status.status

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['data']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clc_submitted_cases), len(response_data['cases']))
        # Assert Case Type
        for case in response_data['cases']:
            case_type = Case.objects.filter(pk=case['id']).values_list('type', flat=True)[0]
            self.assertEqual(case_type, 'clc_query')

    def test_get_cases_no_filter_sort_by_status_ascending(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases sorted by case_type
        Then all Cases are sorted in ascending order and returned
        """

        # Arrange
        all_cases = self.application_cases + self.clc_cases
        all_cases = [
            {
                'case': str(case.id),
                'status': case.application.status.priority if case.application is not None else
                case.query.status.priority
            }
            for case in all_cases
        ]
        all_cases_sorted = sorted(all_cases, key=lambda k: k['status'])
        url = self.url + '?sort=status'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['data']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_cases), len(response_data['cases']))
        # Assert ordering
        for case, expected_case in zip(response_data['cases'], all_cases_sorted):
            self.assertEqual(case['id'], expected_case['case'])

    def test_get_app_type_cases_sorted_by_status_descending(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view all Cases sorted by case_type
        Then all Cases are sorted in descending order and returned
        """

        # Arrange
        application_cases_sorted = sorted(
            [{'case': str(case.id), 'status': case.application.status.priority} for case in self.application_cases],
            key=lambda k: k['status'],
            reverse=True
        )

        url = self.url + '?case_type=application&sort=-status'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['data']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.application_cases), len(response_data['cases']))
        for case, expected_case in zip(response_data['cases'], application_cases_sorted):
            # Assert Case Type
            case_type = Case.objects.filter(pk=case['id']).values_list('type', flat=True)[0]
            self.assertEqual(case_type, 'application')
            # Assert ordering
            self.assertEqual(case['id'], expected_case['case'])
