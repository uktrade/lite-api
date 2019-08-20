from django.urls import reverse
from rest_framework import status

from cases.models import Case
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status
from test_helpers.clients import DataTestClient


class CasesFilterAndSortTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.url = reverse('queues:queue', kwargs={'pk': self.queue.pk})

        self.application_cases = []
        for app_status in CaseStatusEnum.choices:
            case = self.create_standard_application_case(self.exporter_user.organisation, 'Example Application')
            case.application.status = get_case_status_from_status(app_status)
            case.application.save(update_fields=['status'])
            self.queue.cases.add(case)
            self.queue.save()
            self.application_cases.append(case)

        self.clc_cases = []
        for clc_status in CaseStatusEnum.choices:
            case = self.create_clc_query_case('Example CLC Query', get_case_status_from_status(clc_status))
            self.queue.cases.add(case)
            self.queue.save()
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
        response_data = response.json()['queue']['cases']

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
        url = self.url + '?case_type=application'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['queue']['cases']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.application_cases))
        # Assert Case Type
        for case in response_data:
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
        response_data = response.json()['queue']['cases']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.clc_cases), len(response_data))

        # Assert Case Type
        for case in response_data:
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
        response_data = response.json()['queue']['cases']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.clc_cases))
        # Assert Case Type
        for case in response_data:
            case_type = Case.objects.filter(pk=case['id']).values_list('type', flat=True)[0]
            self.assertEqual(case_type, 'clc_query')

    def test_get_all_cases_queue_submitted_status_and_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view All Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        case_status = get_case_status_from_status(CaseStatusEnum.SUBMITTED)
        clc_submitted_cases = list(filter(lambda case: case.clc_query.status == case_status, self.clc_cases))
        url = reverse('queues:queue', kwargs={'pk': 'de13c40a-b330-4d77-8304-57ac12326e5a'}
                      ) + '?case_type=CLC%20query&status=' + case_status.status + '&sort={"status":"asc"}'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['queue']['cases']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clc_submitted_cases), len(response_data))
        # Assert Case Type
        for case in response_data:
            case_type = Case.objects.filter(pk=case['id']).values_list('type', flat=True)[0]
            self.assertEqual('clc_query', case_type)

    def test_get_submitted_status_and_clc_type_cases(self):
        """
        Given multiple Cases exist with different statuses and case-types
        When a user requests to view Cases of type 'CLC query'
        Then only Cases of that type are returned
        """

        # Arrange
        case_status = get_case_status_from_status(CaseStatusEnum.SUBMITTED)
        clc_submitted_cases = list(filter(lambda case: case.clc_query.status == case_status, self.clc_cases))
        url = self.url + '?case_type=clc_query&status=' + case_status.status

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['queue']['cases']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clc_submitted_cases), len(response_data))
        # Assert Case Type
        for case in response_data:
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
                case.clc_query.status.priority
             }
            for case in all_cases
        ]
        all_cases_sorted = sorted(all_cases, key=lambda k: k['status'])
        url = self.url + '?sort={"status":"asc"}'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['queue']['cases']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_cases), len(response_data))
        # Assert ordering
        for i in range(0, len(response_data)):
            self.assertEqual(response_data[i]['id'], all_cases_sorted[i]['case'])

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

        url = self.url + '?case_type=application&sort={"status":"desc"}'

        # Act
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()['queue']['cases']

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.application_cases), len(response_data))
        for i in range(0, len(response_data)):
            # Assert Case Type
            case_type = Case.objects.filter(pk=response_data[i]['id']).values_list('type', flat=True)[0]
            self.assertEqual(case_type, 'application')
            # Assert ordering
            self.assertEqual(response_data[i]['id'], application_cases_sorted[i]['case'])
