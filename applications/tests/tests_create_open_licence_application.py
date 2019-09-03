from django.urls import reverse
from rest_framework import status

from applications.enums import ApplicationLicenceType, ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.models import Application
from drafts.models import Draft, SiteOnDraft
from queues.models import Queue
from test_helpers.clients import DataTestClient


class ApplicationsTests(DataTestClient):

    def setUp(self):
        super().setUp()

    url = reverse('applications:applications')

    def test_create_application_case_and_addition_to_queue(self):
        """
        Test whether we can create a open licence application
        """
        draft = self.create_open_draft(self.organisation)

        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 0)

        data = {'id': draft.id}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        application = Application.objects.get(pk=draft.id)

        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 1)
        self.assertEqual(application.end_user, draft.end_user)
