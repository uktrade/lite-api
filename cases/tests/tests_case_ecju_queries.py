import json

from django.test import tag
from django.urls import reverse
from rest_framework import status

from cases.models import EcjuQuery
from test_helpers.clients import DataTestClient


class CaseEcjuQueriesTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.case2 = self.create_standard_application_case(self.organisation)
        self.no_ecju_queries_case = self.create_standard_application_case(self.organisation)

        self.url = reverse('cases:case_ecju_queries', kwargs={'pk': self.case.id})

        ecju_query = EcjuQuery(question='ECJU Query 1', case=self.case, raised_by_user=self.gov_user)
        ecju_query.save()

        self.team_2 = self.create_team('TAU')
        self.gov_user2_email = 'bob@slob.com'
        self.gov_user_2 = self.create_gov_user(self.gov_user2_email, self.team_2)

        ecju_query = EcjuQuery(question='ECJU Query 2', case=self.case, response='I have a response',
                               raised_by_user=self.gov_user_2, responded_by_user=self.exporter_user)
        ecju_query.save()
        ecju_query = EcjuQuery(question='ECJU Query 3', case=self.case2, raised_by_user=self.gov_user)
        ecju_query.save()

    def test_view_case_with_ecju_queries_as_gov_user_successful(self):
        """
        Given a case with ECJU queries on it
        When a gov user requests the ECJU queries for the case
        Then the request is successful
        """
        # Act
        response = self.client.get(self.url, **self.gov_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_case_with_ecju_queries_as_exporter_user_successful(self):
        """
        Given a case with ECJU queries on it
        When an exporter user requests the ECJU queries for the case
        Then the request is successful
        """
        # Act
        response = self.client.get(self.url, **self.exporter_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_correct_ecju_query_details_are_returned_to_gov_user(self):
        """
        Given a case with ECJU queries
        When a gov user requests the ECJU queries for the case
        Then the expected ECJU queries and properties are returned
        """
        # Act
        response = self.client.get(self.url, **self.gov_headers)

        # Assert
        response_json = response.json()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json.get('ecju_queries')), 2)

        returned_ecju_query_1 = response_json.get('ecju_queries')[0]
        self.assertEqual(returned_ecju_query_1.get('question'), 'ECJU Query 1')
        self.assertEqual(returned_ecju_query_1.get('response'), None)

        returned_ecju_query_2 = response_json.get('ecju_queries')[1]
        self.assertEqual(returned_ecju_query_2.get('question'), 'ECJU Query 2')
        self.assertEqual(returned_ecju_query_2.get('response'), 'I have a response')

    def test_correct_ecju_query_details_are_returned_to_exporter_user(self):
        """
        Given a case with ECJU queries
        When an exporter user requests the ECJU queries for the case
        Then the expected ECJU queries and properties are returned
        """
        # Act
        response = self.client.get(self.url, **self.exporter_headers)

        # Assert
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json.get('ecju_queries')), 2)

        returned_ecju_query_1 = response_json.get('ecju_queries')[0]
        self.assertEqual(returned_ecju_query_1.get('question'), 'ECJU Query 1')
        self.assertEqual(returned_ecju_query_1.get('response'), None)
        self.assertEqual(returned_ecju_query_1.get('team')['name'], 'Admin')
        # We can't predict exactly when the query is created so we settle for the fact that its set
        self.assertIsNotNone(returned_ecju_query_1.get('created_at'))

        returned_ecju_query_2 = response_json.get('ecju_queries')[1]
        self.assertEqual(returned_ecju_query_2.get('question'), 'ECJU Query 2')
        self.assertEqual(returned_ecju_query_2.get('response'), 'I have a response')
        self.assertEqual(returned_ecju_query_2.get('team')['name'], 'TAU')
        # We can't predict exactly when the query is created so we settle for the fact that its set
        self.assertIsNotNone(returned_ecju_query_1.get('created_at'))

    def test_view_case_without_ecju_queries(self):
        """
        Given a case with no ECJU queries
        When a gov user requests the ECJU queries for the case
        Then the request is successful and an empty list is returned
        """
        # Assemble
        no_queries_url = reverse('cases:case_ecju_queries', kwargs={'pk': self.no_ecju_queries_case.id})

        # Act
        response = self.client.get(no_queries_url, **self.gov_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get('ecju_queries')), 0)


class EcjuQueriesCreateTest(DataTestClient):

    def test_gov_user_can_create_ecju_queries(self):
        """
        Given a Case
        When a gov user adds an ECJU query to the case with valid data
        Then the request is successful and the ECJU query is saved
        """
        case = self.create_standard_application_case(self.organisation)
        url = reverse('cases:case_ecju_queries', kwargs={'pk': case.id})
        data = {
            'question': 'Test ECJU Query question?'
        }

        response = self.client.post(url, data, **self.gov_headers)
        response_data = json.loads(response.content)
        ecju_query = EcjuQuery.objects.get(case=case)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data['ecju_query_id'], str(ecju_query.id))
        self.assertEqual('Test ECJU Query question?', ecju_query.question)

    def test_gov_user_can_create_ecju_queries_on_query_cases(self):
        """
        Given a query case
        When a gov user adds an ECJU query to the case with valid data
        Then the request is successful and the ECJU query is saved
        """
        case = self.create_clc_query('Query', self.organisation).case.get()
        url = reverse('cases:case_ecju_queries', kwargs={'pk': case.id})
        data = {
            'question': 'Test ECJU Query question?'
        }

        # Act
        response = self.client.post(url, data, **self.gov_headers)
        response_data = json.loads(response.content)
        ecju_query = EcjuQuery.objects.get(case=case)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(str(ecju_query.id), response_data['ecju_query_id'])
        self.assertEqual(ecju_query.question, data['question'])

    def test_bad_data_create_fail(self):
        """
        Given a Case
        When a gov user adds an ECJU query to the case with invalid data
        Then the request fails
        """
        # Not possible to parameterize due to need to refer to self.case
        case = self.create_standard_application_case(self.organisation)
        url = reverse('cases:case_ecju_queries', kwargs={'pk': case.id})
        test_data_list = [
            {'question': ''},
            {'question': None},
            {'question': 'a' * 5001}
        ]

        for test_data in test_data_list:
            # Act
            response = self.client.post(url, test_data, **self.gov_headers)

            # Assert
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_gov_user_can_get_an_individual_ecju_query(self):
        """
        Given an ECJU query
        When a gov user requests the ECJU query by ID
        Then the request is successful and the details of the ECJU query are returned
        """
        case = self.create_standard_application_case(self.organisation)
        ecju_query = EcjuQuery(question='Ble', case=case, raised_by_user=self.gov_user)
        ecju_query.save()

        url = reverse('cases:case_ecju_query', kwargs={'pk': case.id, 'ecju_pk': ecju_query.id})

        # Act
        response = self.client.get(url, **self.gov_headers)

        # Assert
        response_data = json.loads(response.content)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(str(ecju_query.id), response_data['ecju_query']['id'])
        self.assertEqual(str(ecju_query.question), response_data['ecju_query']['question'])
        self.assertEqual(ecju_query.response, None)
        self.assertEqual(str(ecju_query.case.id), response_data['ecju_query']['case'])

    def test_raise_ecju_queries_creates_audit(self):
        """
        Given a case with no ECJU queries
        When a gov user raises an ECJU query for the case
        And the request is successful
        Then an audit entry can be retrieved
        """
        case = self.create_standard_application_case(self.organisation)
        ecju_query = EcjuQuery(question='Bleh', case=case, raised_by_user=self.gov_user)
        ecju_query.save()
        url = reverse('cases:activity', kwargs={'pk': case.pk})

        # Act
        response = self.client.get(url, **self.gov_headers)
        activity = response.json().get('activity')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(activity), 1)
        self.assertEqual('ecju_query', activity[0]['type'])
        self.assertEqual(ecju_query.question, activity[0]['data'])
        self.assertEqual(ecju_query.raised_by_user.get_full_name(), activity[0]['user']['first_name'] + ' '
                         + activity[0]['user']['last_name'])
