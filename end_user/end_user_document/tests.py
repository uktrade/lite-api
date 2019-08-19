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
        self.url_draft_with_user = reverse('drafts:end_user_documents', kwargs={'pk': self.draft.id})

        self.draft_no_user = self.test_helper.complete_draft('Superdraft2', self.org)
        self.url_no_user = reverse('drafts:end_user_documents', kwargs={'pk': self.draft_no_user.id})

        self.data = [{"name": "file123.pdf",
                 "s3_key": "file123_12345678.pdf",
                 "size": 476,
                 "description": "Description 58398"}]

    # if POST - end-user set - GET returns correct data
    @mock.patch('documents.tasks.prepare_document.now')
    def test_correct_data_get_document(self, prepare_document_function):
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        response = self.client.get(self.url_draft_with_user, **self.exporter_headers)

        # assert
        response_data = response.json()['document']
        expected = self.data[0]
        self.assertEqual(response_data['name'], expected['name'])
        self.assertEqual(response_data['s3_key'], expected['s3_key'])
        self.assertEqual(response_data['size'], expected['size'])
        self.assertEqual(response_data['description'], expected['description'])

    # if GET - end-user not set - return 400
    def test_status_code_get_document_no_user(self):
        # act
        response = self.client.get(self.url_no_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # if POST - end-user not set - return 400
    @mock.patch('documents.tasks.prepare_document.now')
    def test_status_code_post_no_user(self, prepare_document_function):
        # act
        response = self.client.post(self.url_no_user, data=self.data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # if DELETE - end-user not set - return 400
    def test_status_code_delete_no_user(self):
        # act
        response = self.client.delete(self.url_no_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # if GET - document not set - return None
    def test_status_code_get_document_not_exist(self):
        # act
        response = self.client.get(self.url_draft_with_user, **self.exporter_headers)

        # assert
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(None, response.json()['document'])

    # if POST - document not set - return 201
    @mock.patch('documents.tasks.prepare_document.now')
    def test_status_code_post_document_not_exist(self, mock_obj):
        # act
        response = self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # if DELETE - document not set - return 400
    def test_status_code_delete_document_not_exist(self):
        # act
        response = self.client.delete(self.url_draft_with_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # if POST - document exist - return 400
    @mock.patch('documents.tasks.prepare_document.now')
    def test_status_code_post_document_exists(self, mock_obj):
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        response = self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # if DELETE - document exist - return 204
    @mock.patch('documents.tasks.prepare_document.now')
    @mock.patch('documents.models.Document.delete_s3')
    def test_status_code_delete_document_exists(self, delete_s3_mock, prepare_document_now_mock):
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        response = self.client.delete(self.url_draft_with_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # if GET - document exist - return 200
    @mock.patch('documents.tasks.prepare_document.now')
    def test_status_code_get_document_exists(self, mock_obj):
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        response = self.client.get(self.url_draft_with_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

