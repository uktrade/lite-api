from unittest import mock
from uuid import uuid4

from django.urls import reverse
from rest_framework import status

from end_user.document.models import EndUserDocument
from test_helpers.clients import DataTestClient

test_file = "dog.jpg"

# TODO: Fix S3 mocking for running tests in CircleCI

class EndUserDocumentTests(DataTestClient):

    def setUp(self):
        super().setUp()

        self.draft = self.create_standard_draft_without_end_user_document(self.organisation, 'Drafty Draft')
        self.url_draft_with_user = reverse('drafts:end_user_document',
                                           kwargs={'pk': self.draft.id, 'eu_pk': self.draft.end_user.id})

        self.draft_no_user = self.create_draft(self.organisation, 'Dafty daft')
        self.url_no_user = reverse('drafts:end_user_document',
                                   kwargs={'pk': self.draft_no_user.id, 'eu_pk': uuid4()})

        self.data = {"name": test_file,
                 "s3_key": test_file,
                 "size": 476}

    @mock.patch('documents.tasks.prepare_document.now')
    def test_correct_data_get_document(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached end user document
        """
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        response = self.client.get(self.url_draft_with_user, **self.exporter_headers)

        # assert
        response_data = response.json()['document']
        expected = self.data
        self.assertEqual(response_data['name'], expected['name'])
        self.assertEqual(response_data['s3_key'], expected['s3_key'])
        self.assertEqual(response_data['size'], expected['size'])

    def test_status_code_get_document_no_user(self):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to retrieve a document
        Then a 400 BAD REQUEST is returned
        """
        # act
        response = self.client.get(self.url_no_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('documents.tasks.prepare_document.now')
    def test_status_code_post_no_user(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to submit a document
        Then a 400 BAD REQUEST is returned
        """
        # act
        response = self.client.post(self.url_no_user, data=self.data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_code_delete_no_user(self):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to delete a document
        Then a 400 BAD REQUEST is returned
        """
        # act
        response = self.client.delete(self.url_no_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_code_get_document_not_exist(self):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user does not have a document attached
        When there is an attempt to get a document
        Then a 404 NOT FOUND is returned
        And the response contains a null document
        """
        # act
        response = self.client.get(self.url_draft_with_user, **self.exporter_headers)

        # assert
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual(None, response.json()['document'])

    @mock.patch('documents.tasks.prepare_document.now')
    def test_status_code_post_document_not_exist(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user does not have a document attached
        When a document is submitted
        Then a 201 CREATED is returned
        """
        # act
        response = self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_status_code_delete_document_not_exist(self):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to delete a document
        Then a 400 BAD REQUEST is returned
        """
        # act
        response = self.client.delete(self.url_draft_with_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('documents.tasks.prepare_document.now')
    def test_status_code_post_document_exists(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to post a document
        Then a 400 BAD REQUEST is returned
        """
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        response = self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('documents.tasks.prepare_document.now')
    def test_only_one_document_exists_even_when_posting_multiple_documents(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to post a document
        Then only a single document exists
        """
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # assert
        self.assertEqual(1, len(EndUserDocument.objects.all()))

    @mock.patch('documents.tasks.prepare_document.now')
    @mock.patch('documents.models.Document.delete_s3')
    def test_status_code_delete_document_exists(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to delete the document
        Then 204 NO CONTENT is returned
        """
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        response = self.client.delete(self.url_draft_with_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @mock.patch('documents.tasks.prepare_document.now')
    def test_status_code_get_document_exists(self, mock_obj):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When the document is retrieved
        Then 200 OK is returned
        """
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        response = self.client.get(self.url_draft_with_user, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch('documents.models.Document.delete_s3')
    @mock.patch('documents.tasks.prepare_document.now')
    def test_delete_end_user_document_calls_delete_s3(self, prepare_document_function, delete_s3_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to delete the document
        Then the function to delete document from S3 is called
        """
        # assemble
        self.client.post(self.url_draft_with_user, data=self.data, **self.exporter_headers)

        # act
        self.client.delete(self.url_draft_with_user, **self.exporter_headers)

        # assert
        delete_s3_function.assert_called_once()
