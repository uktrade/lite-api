from unittest import mock
from django.urls import reverse
from rest_framework import status
from test_helpers.clients import DataTestClient


class DraftEndUserDocumentsTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Superdraft', self.org)
        # self.end_user = self.test_helper.create_end_user("Mr. Kim", self.org)
        self.url = reverse('drafts:end_user_documents', kwargs={'pk': self.draft.id})

        self.draft_no_user = self.test_helper.complete_draft('Superdraft2', self.org)
        self.url_no_user = reverse('drafts:end_user_documents', kwargs={'pk': self.draft_no_user.id})

        self.data = [{"name": "file123.pdf",
                 "s3_key": "file123_12345678.pdf",
                 "size": 476,
                 "description": "Description 58398"}]

    @mock.patch('documents.tasks.prepare_document.now')
    def test_get_post_delete_doc(self, prepare_document_function):
        response = self.client.post(self.url, data=self.data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()['documents'][0]
        expected = self.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['name'], expected['name'])
        self.assertEqual(response_data['s3_key'], expected['s3_key'])
        self.assertEqual(response_data['size'], expected['size'])
        self.assertEqual(response_data['description'], expected['description'])

        response = self.client.delete(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # if DELETE/POST/GET - end-user not set - return 400
    def test_get_no_user(self):
        # act
        response = self.client.get(self.url_no_user, **self.exporter_headers)
        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('documents.tasks.prepare_document.now')
    def test_post_no_user(self, prepare_document_function):
        # act
        response = self.client.post(self.url_no_user, data=self.data, **self.exporter_headers)
        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_no_user(self):
        # act
        response = self.client.delete(self.url_no_user, **self.exporter_headers)
        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    # if GET - document not set - return 404
    # if POST - document not set - return 201
    # if DELETE - document not set - return 400

    # if POST - document exist - return 400
    # if DELETE - document exist - return 204
    # if GET - document exist - return 200

