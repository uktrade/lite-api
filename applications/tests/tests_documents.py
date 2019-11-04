import uuid
from unittest import mock
from django.urls import reverse

from static.statuses.libraries.get_case_status import get_case_status_by_status
from applications.libraries.case_status_helpers import get_read_only_case_statuses, get_editable_case_statuses
from test_helpers.clients import DataTestClient


class DraftDocumentTests(DataTestClient):

    def setUp(self):
        super().setUp()

        self.draft = self.create_standard_application(self.organisation, 'Draft')
        self.url_draft = reverse('applications:application_documents', kwargs={'pk': self.draft.id})
        self.test_filename = 'dog.jpg'

        self.editable_case_statuses = get_editable_case_statuses()
        self.read_only_case_statuses = get_read_only_case_statuses()

        self.data = {'name': self.test_filename,
                     's3_key': self.test_filename,
                     'size': 476,
                     'description': 'banana cake 1'
                     }

        self.data2 = {'name': self.test_filename + '2',
                      's3_key': self.test_filename,
                      'size': 476,
                      'description': 'banana cake 2'
                      }

    @mock.patch('documents.tasks.prepare_document.now')
    def test_upload_document_on_unsubmitted_application(self, mock_prepare_doc):
        """ Test success in adding a document to an unsubmitted application. """
        self.client.post(self.url_draft, data=self.data, **self.exporter_headers)

        response = self.client.get(self.url_draft, **self.exporter_headers)
        response_data = response.json()['documents'][1]

        self.assertEqual(response_data['name'], self.data['name'])
        self.assertEqual(response_data['s3_key'], self.data['s3_key'])
        self.assertEqual(response_data['size'], self.data['size'])
        self.assertEqual(response_data['description'], self.data['description'])

    @mock.patch('documents.tasks.prepare_document.now')
    def test_upload_multiple_documents_on_unsubmitted_application(self, mock_prepare_doc):
        """ Test success in adding multiple documents to an unsubmitted application. """
        self.client.post(self.url_draft, data=self.data, **self.exporter_headers)
        self.client.post(self.url_draft, data=self.data2, **self.exporter_headers)

        response = self.client.get(self.url_draft, **self.exporter_headers)
        response_data = response.json()['documents']
        self.assertEqual(len(response_data), 3)

        document1 = response_data[1]
        self.assertEqual(self.data['name'], document1['name'])
        self.assertEqual(self.data['s3_key'], document1['s3_key'])
        self.assertEqual(self.data['size'], document1['size'])
        self.assertEqual(self.data['description'], document1['description'])

        document2 = response_data[2]
        self.assertEqual(self.data2['name'], document2['name'])
        self.assertEqual(self.data2['s3_key'], document2['s3_key'])
        self.assertEqual(self.data2['size'], document2['size'])
        self.assertEqual(self.data2['description'], document2['description'])

    @mock.patch('documents.tasks.prepare_document.now')
    @mock.patch('documents.models.Document.delete_s3')
    def test_delete_individual_draft_document(self, mock_delete_s3, mock_prepare_doc):
        """ Test success in deleting a document from an unsubmitted application. """
        self.client.post(self.url_draft, data=self.data, **self.exporter_headers)
        response = self.client.get(self.url_draft, **self.exporter_headers)

        url = reverse('applications:application_document',
                      kwargs={'pk': self.draft.id, 'doc_pk': response.json()['documents'][0]['id']})

        self.client.delete(url, **self.exporter_headers)
        mock_delete_s3.assert_called_once()

        response = self.client.get(self.url_draft, **self.exporter_headers)
        self.assertEqual(len(response.json()['documents']), 1)

    def test_get_individual_draft_document(self):
        """ Test success in downloading a document from an unsubmitted application. """
        application_document = self.draft.applicationdocument_set.first()
        url = reverse('applications:application_document',
                      kwargs={'pk': self.draft.id, 'doc_pk': application_document.id})

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.json()['document']['name'], application_document.name)
        self.assertEqual(response.json()['document']['s3_key'], application_document.s3_key)
        self.assertEqual(response.json()['document']['size'], application_document.size)

    @mock.patch('documents.tasks.prepare_document.now')
    def test_add_document_when_application_in_editable_state_success(self, mock_prepare_doc):
        """ Test success in adding a document when an application is in an editable status. """
        for status in self.editable_case_statuses:
            application = self.create_standard_application(self.organisation)
            application.status = get_case_status_by_status(status)
            application.save()

            url = reverse('applications:application_documents', kwargs={'pk': application.id})
            response = self.client.post(url, data=self.data, **self.exporter_headers)

            self.assertEqual(response.status_code, 201)
            self.assertEqual(application.applicationdocument_set.count(), 2)

    @mock.patch('documents.tasks.prepare_document.now')
    def test_delete_document_when_application_in_editable_state_success(self, mock_prepare_doc):
        """ Test success in deleting a document when an application is in an editable status. """
        for status in self.editable_case_statuses:
            application = self.create_standard_application(self.organisation)
            application.status = get_case_status_by_status(status)
            application.save()

            url = reverse('applications:application_document',
                          kwargs={'pk': application.id, 'doc_pk': application.applicationdocument_set.first().id})

            response = self.client.delete(url, **self.exporter_headers)
            self.assertEqual(response.status_code, 204)
            self.assertEqual(application.applicationdocument_set.count(), 0)

    def test_add_document_when_application_in_read_only_state_failure(self):
        """ Test failure in adding an additional document when an application is in a read-only status. """
        for status in self.read_only_case_statuses:
            application = self.create_standard_application(self.organisation)
            application.status = get_case_status_by_status(status)
            application.save()

            url = reverse('applications:application_documents', kwargs={'pk': application.id})
            response = self.client.post(url, data=self.data, **self.exporter_headers)

            self.assertEqual(response.status_code, 400)
            self.assertEqual(application.applicationdocument_set.count(), 1)

    @mock.patch('documents.tasks.prepare_document.now')
    @mock.patch('documents.models.Document.delete_s3')
    def test_delete_document_when_application_in_read_only_state_failure(self, mock_delete_s3, mock_prepare_doc):
        """ Test failure in deleting a document when an application is in a read-only status. """
        for status in self.read_only_case_statuses:
            application = self.create_standard_application(self.organisation)
            application.status = get_case_status_by_status(status)
            application.save()

            url = reverse('applications:application_document', kwargs={'pk': application.id, 'doc_pk': uuid.uuid4()})
            response = self.client.delete(url, **self.exporter_headers)

            self.assertEqual(response.status_code, 400)
            self.assertEqual(application.applicationdocument_set.count(), 1)
