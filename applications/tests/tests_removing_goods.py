from django.urls import reverse
from rest_framework import status

from applications.models import GoodOnApplication
from test_helpers.clients import DataTestClient


class RemovingGoodsOffDraftsTests(DataTestClient):

    def test_remove_a_good_from_draft_success(self):
        """
        Given a standard application with a good
        When I attempt to delete the good from the application
        Then the good is deleted
        """
        draft = self.create_standard_draft(self.organisation)

        url = reverse('applications:good_on_application',
                      kwargs={'good_on_application_pk': self.good_on_application.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(GoodOnApplication.objects.filter(application=draft).count(), 0)

    def test_remove_a_good_that_does_not_exist_from_draft(self):
        """
        Given a standard application with a good
        When I attempt to delete a good that doesn't exist
        Then the delete operation returns a not found response
        And no goods are deleted
        """
        draft = self.create_standard_draft(self.organisation)

        url = reverse('applications:good_on_application',
                      kwargs={'good_on_application_pk': "7070dc05-0afa-482c-b4f7-ae0a8943e53c"})  # Imaginary UUID

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(GoodOnApplication.objects.filter(application=draft).count(), 1)

    def test_remove_a_good_from_draft_as_gov_user_failure(self):
        draft = self.create_standard_draft(self.organisation)

        url = reverse('applications:good_on_application',
                      kwargs={'good_on_application_pk': self.good_on_application.id})

        response = self.client.delete(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(GoodOnApplication.objects.filter(application=draft).count(), 1)
