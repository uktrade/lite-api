from unittest import mock
from django.urls import reverse
from test_helpers.clients import DataTestClient


class DraftDocumentTests(DataTestClient):

    def setUp(self):
        super().setUp()

        self.draft = self.create_standard_draft_without_end_user_document(self.organisation, 'Draft')
        self.url_draft = reverse('drafts:draft_documents', kwargs={'pk': self.draft.id})
        self.test_filename = "dog.jpg"

        self.data = {"name": self.test_filename,
                     "s3_key": self.test_filename,
                     "size": 476,
                     "draft": self.draft.id,
                     "description": "banana cake"
                     }

        self.data2 = {"name": self.test_filename + "2",
                      "s3_key": self.test_filename,
                      "size": 476,
                      "draft": self.draft.id,
                      "description": "banana cake"
                      }

    @mock.patch('documents.tasks.prepare_document.now')
    def test_upload_draft_document(self, mock_prepare_doc):
        """
        Given a standard draft has been created
        When a draft document is uploaded
        Then the document is available on the draft
        """
        self.client.post(self.url_draft, data=self.data, **self.exporter_headers)

        response = self.client.get(self.url_draft, **self.exporter_headers)
        response_data = response.json()['documents'][0]

        self.assertEqual(response_data['name'], self.data['name'])
        self.assertEqual(response_data['s3_key'], self.data['s3_key'])
        self.assertEqual(response_data['size'], self.data['size'])
        self.assertEqual(response_data['description'], self.data['description'])
        self.assertEqual(response_data['draft_id'], str(self.data['draft']))

    @mock.patch('documents.tasks.prepare_document.now')
    def test_upload_multiple_draft_documents(self, mock_prepare_doc):
        """
        Given a standard draft has been created
        When multiple draft documents are uploaded
        Then the documents are available on the draft
        """

        self.client.post(self.url_draft, data=self.data, **self.exporter_headers)
        self.client.post(self.url_draft, data=self.data2, **self.exporter_headers)

        response = self.client.get(self.url_draft, **self.exporter_headers)

        response_data = response.json()['documents']
        self.assertEqual(len(response_data), 2)

        document1 = response_data[0]
        self.assertEqual(self.data['name'], document1['name'])
        self.assertEqual(self.data['s3_key'], document1['s3_key'])
        self.assertEqual(self.data['size'], document1['size'])
        self.assertEqual(self.data['description'], document1['description'])
        self.assertEqual(str(self.data['draft']), document1['draft_id'])

        document2 = response_data[1]
        self.assertEqual(self.data2['name'], document2['name'])
        self.assertEqual(self.data2['s3_key'], document2['s3_key'])
        self.assertEqual(self.data2['size'], document2['size'])
        self.assertEqual(self.data2['description'], document2['description'])
        self.assertEqual(str(self.data2['draft']), document2['draft_id'])

    @mock.patch('documents.tasks.prepare_document.now')
    @mock.patch('documents.models.Document.delete_s3')
    def test_delete_individual_draft_document(self, mock_delete_s3, mock_prepare_doc):
        """
        Given a standard draft has been created
        And multiple draft documents have been uploaded
        When there is an attempt to delete an individual document
        Then the individual document is no longer available on the draft
        """

        self.client.post(self.url_draft, data=self.data, **self.exporter_headers)
        self.client.post(self.url_draft, data=self.data2, **self.exporter_headers)

        response = self.client.get(self.url_draft, **self.exporter_headers)

        url = reverse('drafts:draft_document', kwargs={'pk': self.draft.id,
                                                       'doc_pk': response.json()['documents'][0]['id']})

        self.client.delete(url, **self.exporter_headers)

        mock_delete_s3.assert_called_once()
        response = self.client.get(self.url_draft, **self.exporter_headers)
        self.assertEqual(len(response.json()['documents']), 1)
