from django.urls import reverse
from rest_framework import status

from cases.models import CaseDocument
from test_helpers.clients import DataTestClient


class CaseDocumentsTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.case = self.create_case('case')
        self.url = reverse('cases:documents', kwargs={'pk': self.case.id})

    # def test_successfully_add_a_document(self):

    def test_can_view_all_documents_on_a_case(self):
        self.create_case_document(case=self.case, user=self.user, name='doc1')
        self.create_case_document(case=self.case, user=self.user, name='doc2')

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['documents']), 2)
