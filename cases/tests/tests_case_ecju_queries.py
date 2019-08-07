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
        self.application = self.submit_draft(self.draft)
        self.application2 = self.submit_draft(self.draft2)
        self.case = Case.objects.get(application=self.application)
        self.case2 = Case.objects.get(application=self.application2)
        self.url = reverse('cases:case_ecju_queries', kwargs={'pk': self.case.id})

        ecju_query = EcjuQuery(question='ECJU Query 1', case=self.case)
        ecju_query.save()
        ecju_query = EcjuQuery(question='ECJU Query 2', case=self.case)
        ecju_query.save()
        ecju_query = EcjuQuery(question='ECJU Query 3', case=self.case2)
        ecju_query.save()

    def test_view_ecju_queries_successful(self):
        """
        Given a case with ECJU Queries on it
        When a gov user requests the ECJU Queries for the case
        Then the request is successful and the list of the ECJU queries on the case are returned
        """
        # Assemble

        # Act
        response = self.client.get(self.url, **self.gov_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get('ecju_queries')), 2)
