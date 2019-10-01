from unittest import mock

from django.urls import reverse
from rest_framework import status

from parties.document.models import PartyDocument
from test_helpers.clients import DataTestClient

# TODO: Fix S3 mocking for running tests in CircleCI


class PartyDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.draft = self.create_standard_draft(self.organisation, 'Draft')
        self.url = reverse('drafts:end_user_document', kwargs={'pk': self.draft.id})

        self.draft_no_end_user = self.create_standard_draft(self.organisation, 'No End User Draft')
        PartyDocument.objects.filter(party=self.draft_no_end_user.end_user).delete()
        self.draft_no_end_user.end_user = None
        self.draft_no_end_user.save()
        self.url_no_end_user = reverse('drafts:end_user_document', kwargs={'pk': self.draft_no_end_user.id})

        self.draft_no_end_user_doc = self.create_standard_draft(self.organisation, 'No End User Document Draft')
        PartyDocument.objects.filter(party=self.draft_no_end_user_doc.end_user).delete()
        self.url_no_end_user_doc = reverse('drafts:end_user_document', kwargs={'pk': self.draft_no_end_user_doc.id})

        self.data = {
            'name': 'document_name.pdf',
            's3_key': 's3_keykey.pdf',
            'size': 123456
        }

    @mock.patch('documents.tasks.prepare_document.now')
    def test_correct_data_get_document_end_user(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached end user document
        """

        # act
        response = self.client.get(self.url, **self.exporter_headers)

        # assert
        response_data = response.json()['document']
        expected = self.data
        self.assertEqual(response_data['name'], expected['name'])
        self.assertEqual(response_data['s3_key'], expected['s3_key'])
        self.assertEqual(response_data['size'], expected['size'])

    @mock.patch('documents.tasks.prepare_document.now')
    def test_correct_data_document_ultimate_end_user(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an ultimate end user
        And the ultimate end user has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached ultimate end user document
        """

        # assemble
        self.draft.ultimate_end_users.add(
            self.create_ultimate_end_user('UEU', self.organisation)
        )
        url_ultimate_end_user_doc = reverse(
            'drafts:ultimate_end_user_document',
            kwargs={
                'pk': self.draft.id,
                'ueu_pk': self.draft.ultimate_end_users.first().id
            }
        )
        self.client.post(url_ultimate_end_user_doc, data=self.data, **self.exporter_headers)

        # act
        response = self.client.get(url_ultimate_end_user_doc, **self.exporter_headers)

        # assert
        response_data = response.json()['document']
        expected = self.data
        self.assertEqual(response_data['name'], expected['name'])
        self.assertEqual(response_data['s3_key'], expected['s3_key'])
        self.assertEqual(response_data['size'], expected['size'])

    @mock.patch('documents.tasks.prepare_document.now')
    def test_correct_data_document_consignee(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a consignee
        And the consignee has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached consignee document
        """

        # assemble
        self.draft.consignee = self.create_consignee('Consignee', self.organisation)
        self.draft.save()

        url_consignee_doc = reverse('drafts:consignee_document', kwargs={'pk': self.draft.id})
        self.client.post(url_consignee_doc, data=self.data, **self.exporter_headers)

        # act
        response = self.client.get(url_consignee_doc, **self.exporter_headers)

        # assert
        response_data = response.json()['document']
        expected = self.data
        self.assertEqual(response_data['name'], expected['name'])
        self.assertEqual(response_data['s3_key'], expected['s3_key'])
        self.assertEqual(response_data['size'], expected['size'])

    @mock.patch('documents.tasks.prepare_document.now')
    def test_correct_data_document_third_party(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a third party
        And the third party has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached third party document
        """

        # assemble
        self.draft.third_parties.add(
            self.create_third_party('TP', self.organisation)
        )
        url_third_party_doc = reverse(
            'drafts:third_party_document',
            kwargs={
                'pk': self.draft.id,
                'tp_pk': self.draft.third_parties.first().id
            }
        )
        self.client.post(url_third_party_doc, data=self.data, **self.exporter_headers)

        # act
        response = self.client.get(url_third_party_doc, **self.exporter_headers)

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
        response = self.client.get(self.url_no_end_user, **self.exporter_headers)

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
        response = self.client.post(self.url_no_end_user, data=self.data, **self.exporter_headers)

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
        response = self.client.delete(self.url_no_end_user, **self.exporter_headers)

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
        response = self.client.get(self.url_no_end_user_doc, **self.exporter_headers)

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
        response = self.client.post(self.url_no_end_user_doc, data=self.data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_status_code_delete_document_user_does_not_exist(self):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to delete a document
        Then a 400 BAD REQUEST is returned
        """

        # act
        response = self.client.delete(self.url_no_end_user, **self.exporter_headers)

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
        self.client.post(self.url_no_end_user_doc, data=self.data, **self.exporter_headers)

        # act
        response = self.client.post(self.url_no_end_user_doc, data=self.data, **self.exporter_headers)

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

        # act
        self.client.post(self.url, data=self.data, **self.exporter_headers)

        # assert
        self.assertEqual(PartyDocument.objects.filter(party=self.draft.end_user).count(), 1)

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
        self.client.post(self.url_no_end_user_doc, data=self.data, **self.exporter_headers)

        # act
        response = self.client.delete(self.url_no_end_user_doc, **self.exporter_headers)

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
        self.client.post(self.draft, data=self.data, **self.exporter_headers)

        # act
        response = self.client.get(self.url, **self.exporter_headers)

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
        self.client.post(self.draft, data=self.data, **self.exporter_headers)

        # act
        self.client.delete(self.url, **self.exporter_headers)

        # assert
        delete_s3_function.assert_called_once()
