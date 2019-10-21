from django.urls import reverse
from rest_framework import status

from applications.models import GoodOnApplication
from test_helpers.clients import DataTestClient


# from nose.tools import assert_true
# import requests


class GoodDocumentsTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.good = self.create_controlled_good('this is a good', self.organisation)
        self.url = reverse('goods:documents', kwargs={'pk': self.good.id})

    def test_can_view_all_documents_on_a_good(self):
        self.create_good_document(good=self.good, user=self.exporter_user, organisation=self.organisation,
                                  s3_key='doc1key', name='doc1.pdf')
        self.create_good_document(good=self.good, user=self.exporter_user, organisation=self.organisation,
                                  s3_key='doc2key', name='doc2.pdf')

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['documents']), 2)

    # Circle CI cannot handle this test as the AWS bucket name is invalid
    # @tag('slow')
    # def test_can_remove_document_from_unsubmitted_good(self):
    #     doc1 = self.create_good_document(good=self.good, user=self.exporter_user, s3_key='doc1key', name='doc1.pdf')
    #     self.create_good_document(good=self.good, user=self.exporter_user, s3_key='doc2key', name='doc2.pdf')
    #
    #     url = reverse('goods:document', kwargs={'pk': self.good.id, 'doc_pk': doc1.id})
    #
    #     response = self.client.delete(url, **self.exporter_headers)
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
    #     response = self.client.get(self.url, **self.exporter_headers)
    #     response_data = response.json()
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(response_data['documents']), 1)

    def test_submitted_good_cannot_have_docs_added(self):
        """
        Tests that the good cannot be edited after submission
        """
        draft = self.create_standard_application(self.organisation)
        good_id = GoodOnApplication.objects.get(application=draft).good.id
        self.submit_application(draft)

        url = reverse('goods:documents', kwargs={'pk': good_id})
        data = {}
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submitted_good_cannot_have_docs_removed(self):
        """
        Tests that the good cannot be edited after submission
        """
        draft = self.create_standard_application(self.organisation)
        good = GoodOnApplication.objects.get(application=draft).good
        document_1 = self.create_good_document(good=good,
                                               user=self.exporter_user,
                                               organisation=self.organisation,
                                               s3_key='doc1key',
                                               name='doc1.pdf')
        self.submit_application(draft)

        url = reverse('goods:document', kwargs={'pk': good.id, 'doc_pk': document_1.id})
        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Circle CI does not like calls to live S3
    # TODO: Work in progress
    # def test_add_a_document(self):
    #     data = [{"name": "file123.pdf",
    #              "s3_key": "file123_12345678.pdf",
    #              "size": 476,
    #              "description": "Description 58398"}]
    #
    #     response = self.client.post(self.url, data=data, **self.gov_headers)
    #
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     print('STATUSCODE' + str(response.status_code))
    #     self.assertEqual(CaseDocument.objects.count(), 1)
    #     self.assertEqual(CaseDocument.objects.get().case, self.case)
