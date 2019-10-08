from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from parties.models import EndUser
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class EndUserOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.draft.end_user = None
        self.draft.save()
        self.url = reverse('applications:end_user', kwargs={'pk': self.draft.id})
        self.new_end_user_data = {
            'name': 'Government of Paraguay',
            'address': 'Asuncion',
            'country': 'PY',
            'sub_type': 'government',
            'website': 'https://www.gov.py'
        }

    @parameterized.expand([
        'government',
        'commercial',
        'other'
    ])
    def test_set_end_user_on_draft_successful(self, data_type):
        data = {
            'name': 'Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'sub_type': data_type,
            'website': 'https://www.gov.uk'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.draft.end_user.name, data['name'])
        self.assertEqual(self.draft.end_user.address, data['address'])
        self.assertEqual(self.draft.end_user.country, get_country(data['country']))
        self.assertEqual(self.draft.end_user.sub_type, data_type)
        self.assertEqual(self.draft.end_user.website, data['website'])

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
            'sub_type': 'business',
            'website': 'https://www.americanmary.com'
        }],
    ])
    def test_set_end_user_on_draft_failure(self, data):
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.draft.end_user, None)

    def test_end_user_is_deleted_when_new_one_added(self):
        """
        Given a standard draft has been created
        And the draft contains an end user
        When a new end user is added
        Then the old one is removed
        """
        # assemble
        end_user1 = self.create_end_user('old end user', self.organisation)
        self.draft.end_user = end_user1
        self.draft.save()

        self.client.post(self.url, self.new_end_user_data, **self.exporter_headers)
        self.draft.refresh_from_db()
        end_user2 = self.draft.end_user

        self.assertNotEqual(end_user2, end_user1)
        with self.assertRaises(EndUser.DoesNotExist):
            EndUser.objects.get(id=end_user1.id)

    '''@mock.patch('documents.models.Document.delete_s3')
    @mock.patch('documents.tasks.prepare_document.now')
    def test_end_user_document_is_deleted_when_associated_end_user_is_deleted(self, prep_doc_mock, delete_s3_mock):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user has a document
        When a new end user is added
        Then the previous old user's associated document is deleted
        """
        # assemble
        end_user_1_id = self.draft.end_user.id
        self.document_data = {"name": test_file,
                 "s3_key": test_file,
                 "size": 476,
                 "description": "Description 7538564"}
        self.client.post(reverse('drafts:end_user_document', kwargs={'pk': self.draft.id}),
                         self.document_data, **self.exporter_headers)

        # act
        self.client.post(self.url, self.new_end_user_data, **self.exporter_headers)

        # assert
        with self.assertRaises(EndUserDocument.DoesNotExist):
            EndUserDocument.objects.get(end_user=end_user_1_id)

        delete_s3_mock.assert_called_once()'''

