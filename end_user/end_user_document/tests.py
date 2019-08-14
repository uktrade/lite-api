from django.test import tag
from django.urls import reverse
from rest_framework import status

from drafts.models import GoodOnDraft
from test_helpers.clients import DataTestClient


class DraftEndUserDocumentsTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Superdraft', self.org)
        self.end_user = self.test_helper.create_end_user("Mr. Kim", self.org)
        self.url = reverse('drafts:end_user_documents', kwargs={'pk': self.draft.id})

    def test_can_view_document_on_end_user(self):
        self.create_draft_end_user_document(
            draft=self.draft,
            end_user=self.end_user,
            user=self.exporter_user,
            s3_key='doc1key',
            name='doc1.pdf'
        )
        self.create_draft_end_user_document(
            draft=self.draft,
            end_user=self.end_user,
            user=self.exporter_user,
            s3_key='doc2key',
            name='doc2.pdf'
        )

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        print('RESPONSE DATA', response_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['documents']), 2)



























    # def test_can_remove_document_from_unsubmitted_good(self):
    #     doc1 = self.create_end_user_document(end_user=self.end_user,
    #                                          user=self.exporter_user,
    #                                          s3_key='doc1key',
    #                                          name='doc.pdf')
    #
    #     self.create_end_user_document(end_user=self.end_user,
    #                                   user=self.exporter_user,
    #                                   s3_key='doc1key',
    #                                   name='doc.pdf')
    #
    #     response = self.client.get(self.url, **self.exporter_headers)
    #     response_data = response.json()
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(response_data['documents']), 1)



    #
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
    #
    # def test_submitted_good_cannot_have_docs_added(self):
    #     """
    #     Tests that the good cannot be edited after submission
    #     """
    #     draft = self.test_helper.create_draft_with_good_end_user_and_site('test', self.org)
    #     good_id = GoodOnDraft.objects.get(draft=draft).good.id
    #     self.test_helper.submit_draft(self, draft=draft)
    #
    #     url = reverse('goods:documents', kwargs={'pk': good_id})
    #     data = {}
    #     response = self.client.post(url, data, **self.exporter_headers)
    #
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #
    # def test_submitted_good_cannot_have_docs_removed(self):
    #     """
    #     Tests that the good cannot be edited after submission
    #     """
    #     draft = self.test_helper.create_draft_with_good_end_user_and_site('test', self.org)
    #     good = GoodOnDraft.objects.get(draft=draft).good
    #     doc1 = self.create_good_document(good=self.good, user=self.exporter_user, s3_key='doc1key', name='doc1.pdf')
    #     self.test_helper.submit_draft(self, draft=draft)
    #
    #     url = reverse('goods:document', kwargs={'pk': good.id, 'doc_pk': doc1.id})
    #     response = self.client.delete(url, **self.exporter_headers)
    #
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #
