import json

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.models import Case
from ecju_queries.models import EcjuQuery
from test_helpers.clients import DataTestClient


class FlagsCreateTest(DataTestClient):

    post_url = reverse('ecju_queries:ecju_queries')

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application',
                                                                               self.test_helper.organisation)
        self.application = self.submit_draft(self.draft)
        self.case = Case.objects.get(application=self.application)
        self.post_url = reverse('ecju_queries:ecju_queries')

    def test_gov_user_can_create_ecju_queries(self):
        """
        Given a Case
        When a gov user adds an ECJU query to the case with valid data
        Then the request is successful and the ECJU query is saved
        """
        # Assemble
        data = {
            'question': 'Test ECJU Query question?',
            'case': self.case.id
        }

        # Act
        response = self.client.post(self.post_url, data, **self.gov_headers)

        # Assert
        ecju_query = EcjuQuery.objects.get(case=self.case)
        response_data = json.loads(response.content)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(str(ecju_query.id), response_data['ecju_query_id'])
        self.assertEqual('Test ECJU Query question?', ecju_query.question)

    def test_bad_data_create_fail(self):
        """
        Given a Case
        When a gov user adds an ECJU query to the case with invalid data
        Then the request fails
        """
        # Assemble
        # Not possible to parameterize due to need to refer to self.case
        test_data_list = [
            {'question': '', 'case': self.case.id},
            {'question': 'Why?', 'case': ''},
            {'case': self.case.id},
            {'question': 'Why?'},
            {'question': None, 'case': self.case.id},
            {'question': 'Why?', 'case': None},
            {'question': 'a' * 5001, 'case': self.case.id}
        ]

        for test_data in test_data_list:
            # Act
            response = self.client.post(self.post_url, test_data, **self.gov_headers)

            # Assert
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_gov_user_can_get_an_individual_ecju_query(self):
        """
        Given an ECJU query
        When a gov user requests the ECJU query by ID
        Then the request is successful and the details of the ECJU query are returned
        """
        # Assemble
        ecju_query = EcjuQuery(question='Ble', case=self.case)
        ecju_query.save()

        get_url = reverse('ecju_queries:ecju_query', kwargs={'pk': ecju_query.id})

        # Act
        response = self.client.get(get_url, **self.gov_headers)

        # Assert
        response_data = json.loads(response.content)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(str(ecju_query.id), response_data['ecju_query']['id'])
        self.assertEqual(str(ecju_query.question), response_data['ecju_query']['question'])
        self.assertEqual(ecju_query.response, None)
        self.assertEqual(str(ecju_query.case.id), response_data['ecju_query']['case'])
