from unittest import mock

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from parties.document.models import PartyDocument
from parties.models import Consignee
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class ConsigneeOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)
        self.url = reverse('applications:consignee', kwargs={'pk': self.draft.id})

        self.document_url = reverse('applications:consignee_document', kwargs={'pk': self.draft.id})
        self.new_document_data = {
            'name': 'document_name.pdf',
            's3_key': 's3_keykey.pdf',
            'size': 123456
        }

    @parameterized.expand([
        'government',
        'commercial',
        'other'
    ])
    def test_set_consignee_on_draft_successful(self, data_type):
        """
        Given a standard draft has been created
        And the draft does not yet contain a consignee
        When a new consignee is added
        Then the consignee is successfully added to the draft
        """
        self.draft.consignee = None
        self.draft.save()

        data = {
            'name': 'Government of Paraguay',
            'address': 'Asuncion',
            'country': 'PY',
            'sub_type': data_type,
            'website': 'https://www.gov.py'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.draft.consignee.name, data['name'])
        self.assertEqual(self.draft.consignee.address, data['address'])
        self.assertEqual(self.draft.consignee.country, get_country(data['country']))
        self.assertEqual(self.draft.consignee.sub_type, data_type)
        self.assertEqual(self.draft.consignee.website, data['website'])

    @parameterized.expand([
        [{}],
        [{
            'name': 'Lemonworld Org',
            'address': '3730 Martinsburg Rd, Gambier, Ohio',
            'country': 'US',
            'website': 'https://www.americanmary.com'
        }],
        [{
            'name': 'Lemonworld Org',
            'address': '3730 Martinsburg Rd, Gambier, Ohio',
            'country': 'US',
            'sub_type': 'made-up',
            'website': 'https://www.americanmary.com'
        }],
    ])
    def test_set_consignee_on_draft_failure(self, data):
        """
        Given a standard draft has been created
        And the draft does not yet contain a consignee
        When attempting to add an invalid consignee
        Then the consignee is not added to the draft
        """
        self.draft.consignee = None
        self.draft.save()

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.draft.consignee, None)

    def test_consignee_deleted_when_new_one_added(self):
        """
        Given a standard draft has been created
        And the draft contains a consignee
        When a new consignee is added
        Then the old one is removed
        """
        consignee1 = self.create_consignee('old consignee', self.organisation)
        self.draft.consignee = consignee1
        self.draft.save()
        new_consignee = {
            'name': 'Government of Paraguay',
            'address': 'Asuncion',
            'country': 'PY',
            'sub_type': 'government',
            'website': 'https://www.gov.py'
        }

        self.client.post(self.url, new_consignee, **self.exporter_headers)
        self.draft.refresh_from_db()
        consignee2 = self.draft.consignee

        self.assertNotEqual(consignee2, consignee1)
        with self.assertRaises(Consignee.DoesNotExist):
            Consignee.objects.get(id=consignee1.id)

    def test_set_consignee_on_open_draft_application_failure(self):
        """
        Given a draft open application
        When I try to add a consignee to the application
        Then a 400 BAD REQUEST is returned
        And no consignees have been added
        """
        consignee = self.draft.consignee
        self.draft.consignee = None
        self.draft.save()
        Consignee.objects.filter(pk=consignee.pk).delete()
        data = {
            'name': 'Government of Paraguay',
            'address': 'Asuncion',
            'country': 'PY',
            'sub_type': 'government',
            'website': 'https://www.gov.py'
        }

        open_draft = self.create_open_application(self.organisation)
        url = reverse('applications:consignee', kwargs={'pk': open_draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Consignee.objects.all().count(), 0)

    def test_delete_consignee_on_standard_application_success(self):
        """
        Given a draft standard application
        When I try to delete a consignee from the application
        Then a 204 NO CONTENT is returned
        And the consignee has been deleted
        """
        response = self.client.delete(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Consignee.objects.all().count(), 0)

    def test_delete_consignee_on_standard_application_when_application_has_no_consignee_failure(self):
        """
        Given a draft standard application
        When I try to delete an consignee from the application
        Then a 404 NOT FOUND is returned
        """
        end_user = self.draft.end_user
        self.draft.consignee = None
        self.draft.save()
        Consignee.objects.filter(pk=end_user.pk).delete()

        response = self.client.delete(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch('documents.tasks.prepare_document.now')
    def test_post_consignee_document_success(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a consignee
        And the consignee does not have a document attached
        When a document is submitted
        Then a 201 CREATED is returned
        """
        PartyDocument.objects.filter(party=self.draft.consignee).delete()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch('documents.tasks.prepare_document.now')
    def test_get_consignee_document_success(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a consignee
        And the consignee has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached consignee document
        """
        response = self.client.get(self.document_url, **self.exporter_headers)
        response_data = response.json()['document']
        expected = self.new_document_data

        self.assertEqual(response_data['name'], expected['name'])
        self.assertEqual(response_data['s3_key'], expected['s3_key'])
        self.assertEqual(response_data['size'], expected['size'])

    @mock.patch('documents.tasks.prepare_document.now')
    @mock.patch('documents.models.Document.delete_s3')
    def test_delete_consignee_document_success(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to delete the document
        Then 204 NO CONTENT is returned
        """
        response = self.client.delete(self.document_url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        delete_s3_function.assert_called_once()

    @mock.patch('documents.tasks.prepare_document.now')
    @mock.patch('documents.models.Document.delete_s3')
    def test_delete_consignee_deletes_document_success(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a consignee user
        And the draft contains a consignee document
        When there is an attempt to delete the document
        Then 204 NO CONTENT is returned
        """
        response = self.client.delete(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        delete_s3_function.assert_called_once()