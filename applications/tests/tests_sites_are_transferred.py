from django.urls import reverse
from rest_framework import status

from applications.models import Application, SiteOnApplication
from test_helpers.clients import DataTestClient


class ApplicationsTests(DataTestClient):

    url = reverse('applications:applications')

    def test_that_sites_are_added_to_application_when_submitted(self):
        draft = self.create_standard_draft(self.organisation)

        data = {'id': draft.id}

        response = self.client.post(self.url, data, **self.exporter_headers)
        application = Application.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SiteOnApplication.objects.filter(application=application).count(), 1)
