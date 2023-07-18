from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class CaseDocumentsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.url = reverse("cases:documents", kwargs={"pk": self.case.id})

    def test_can_view_all_documents_on_a_case(self):
        self.create_case_document(case=self.case, user=self.gov_user, name="doc1.pdf")
        self.create_case_document(case=self.case, user=self.gov_user, name="doc2.pdf")

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["documents"]), 2)
