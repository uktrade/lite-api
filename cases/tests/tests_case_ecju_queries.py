from django.urls import reverse
from rest_framework import status

from cases.models import Case
from ecju_queries.models import EcjuQuery
from test_helpers.clients import DataTestClient


class CaseEcjuQueriesTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application',
                                                                               self.test_helper.organisation)
        self.draft2 = self.test_helper.create_draft_with_good_end_user_and_site('Example Application 2',
                                                                                self.test_helper.organisation)
        self.noEcjuQueriesDraft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application 3',
                                                                                self.test_helper.organisation)
        self.application = self.submit_draft(self.draft)
        self.application2 = self.submit_draft(self.draft2)
        self.noEcjuQueriesApplication = self.submit_draft(self.noEcjuQueriesDraft)
        self.case = Case.objects.get(application=self.application)
        self.case2 = Case.objects.get(application=self.application2)
        self.noEcjuQueriesCase = Case.objects.get(application=self.noEcjuQueriesApplication)
        self.url = reverse('cases:case_ecju_queries', kwargs={'pk': self.case.id})

        ecju_query = EcjuQuery(question='ECJU Query 1', case=self.case)
        ecju_query.save()
        ecju_query = EcjuQuery(question='ECJU Query 2', case=self.case, response='I have a response')
        ecju_query.save()
        ecju_query = EcjuQuery(question='ECJU Query 3', case=self.case2)
        ecju_query.save()

    def test_view_case_with_ecju_queries_successful(self):
        """
        Given a case with ECJU queries on it
        When a gov user requests the ECJU queries for the case
        Then the request is successful and the expected number of ECJU queries are returned
        """
        # Assemble

        # Act
        response = self.client.get(self.url, **self.gov_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_correct_ecju_query_details_are_returned(self):
        """
        Given a case with ECJU queries
        When a gov user requests the ECJU queries for the case
        Then the expected ECJU queries and properties are returned
        """
        # Assemble

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

    def test_view_case_without_ecju_queries(self):
        """
        Given a case with no ECJU queries
        When a gov user requests the ECJU queries for the case
        Then the request is successful and an empty list is returned
        """
        # Assemble
        no_queries_url = reverse('cases:case_ecju_queries', kwargs={'pk': self.noEcjuQueriesCase.id})

        # Act
        response = self.client.get(no_queries_url, **self.gov_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get('ecju_queries')), 0)
