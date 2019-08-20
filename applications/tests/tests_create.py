from django.urls import reverse
from rest_framework import status

from applications.enums import ApplicationLicenceType
from applications.models import Application
from queues.models import Queue
from test_helpers.clients import DataTestClient


class ApplicationsTests(DataTestClient):

    url = reverse('applications:applications')

    def test_create_application_case_and_addition_to_queue(self):
        """
        Test whether we can create a draft first and then submit it as an application
        """
        draft = self.create_standard_draft(self.exporter_user.organisation)

        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 0)

        data = {'id': draft.id}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        application = Application.objects.get(pk=draft.id)

        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 1)
        self.assertEqual(application.end_user, draft.end_user)

    def test_create_application_with_invalid_id(self):
        """
        Ensure we cannot create a new application object with an invalid draft id.
        """
        draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'

        self.create_standard_draft(self.exporter_user.organisation)

        data = {'id': draft_id}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_that_cannot_submit_with_no_sites_or_external(self):
        draft = self.create_draft(self.exporter_user.organisation, ApplicationLicenceType.STANDARD_LICENCE)

        data = {'id': draft.id}

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
