from django.urls import reverse
from rest_framework import status

from cases.models import Case
from test_helpers.clients import DataTestClient


class CaseActivityTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application', self.test_helper.organisation)
        self.application = self.submit_draft(self.draft)
        self.case = Case.objects.get(application=self.application)
        self.url = reverse('cases:case_advice', kwargs={'pk': self.case.id})

    # def test_view_case_advice(self):
    #     """
    #     Tests that a gov user can see all advice for a particular case
    #     """
    #     response = self.client.get(self.url, **self.gov_headers)
    #     # response_data = response.json()
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_create_case_advice(self):
    #     """
    #     Tests that a gov user can see all advice for a particular case
    #     """
    #     response = self.client.post(self.url, **self.gov_headers)
    #     response_data = response.json()
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     print(response_data)
