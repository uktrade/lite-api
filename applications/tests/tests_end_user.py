from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from parties.models import EndUser
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class EndUserOnDraftTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)
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
    def test_set_end_user_on_draft_standard_application_successful(self, data_type):
        self.draft.end_user = None
        self.draft.save()
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

    def test_set_end_user_on_draft_open_application_failure(self):
        """
        Given a draft open application
        When I try to add an end user to the application
        Then a 404 NOT FOUND is returned
        And no end users have been added
        """
        self.draft.end_user = None
        self.draft.save()
        pre_test_end_user_count = EndUser.objects.all().count()
        draft_open_application = self.create_open_application(organisation=self.organisation)
        data = {
            'name': 'Government',
            'address': 'Westminster, London SW1A 0AA',
            'country': 'GB',
            'sub_type': 'government',
            'website': 'https://www.gov.uk'
        }
        url = reverse('applications:end_user', kwargs={'pk': draft_open_application.id})

        # act
        response = self.client.post(url, data, **self.exporter_headers)

        # assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(EndUser.objects.all().count(), pre_test_end_user_count)

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
    def test_set_end_user_on_draft_standard_application_failure(self, data):
        self.draft.end_user = None
        self.draft.save()

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
        end_user1 = self.draft.end_user

        self.client.post(self.url, self.new_end_user_data, **self.exporter_headers)
        self.draft.refresh_from_db()
        end_user2 = self.draft.end_user

        self.assertNotEqual(end_user2, end_user1)
        with self.assertRaises(EndUser.DoesNotExist):
            EndUser.objects.get(id=end_user1.id)

    def test_set_end_user_on_open_draft_application_failure(self):
        """
        Given a draft open application
        When I try to add an end user to the application
        Then a 400 BAD REQUEST is returned
        And no end user has been added
        """
        end_user = self.draft.end_user
        self.draft.end_user = None
        self.draft.save()
        EndUser.objects.filter(pk=end_user.pk).delete()
        data = {
            'name': 'Government of Paraguay',
            'address': 'Asuncion',
            'country': 'PY',
            'sub_type': 'government',
            'website': 'https://www.gov.py'
        }

        open_draft = self.create_open_application(self.organisation)
        url = reverse('applications:end_user', kwargs={'pk': open_draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(EndUser.objects.all().count(), 0)

    def test_delete_end_user_on_standard_application_success(self):
        """
        Given a draft standard application
        When I try to delete an end user from the application
        Then a 204 NO CONTENT is returned
        And the end user has been deleted
        """
        response = self.client.delete(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(EndUser.objects.all().count(), 0)

    def test_delete_end_user_on_standard_application_when_application_has_no_end_user_failure(self):
        """
        Given a draft standard application
        When I try to delete an end user from the application
        Then a 404 NOT FOUND is returned
        """
        end_user = self.draft.end_user
        self.draft.end_user = None
        self.draft.save()
        EndUser.objects.filter(pk=end_user.pk).delete()

        response = self.client.delete(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
