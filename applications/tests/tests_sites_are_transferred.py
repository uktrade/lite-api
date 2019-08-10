from django.urls import reverse
from rest_framework import status

from applications.models import Application, SiteOnApplication, ExternalLocationOnApplication
from drafts.models import GoodOnDraft, SiteOnDraft
from static.units.enums import Units
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(DataTestClient):

    url = reverse('applications:applications')

    def test_that_sites_are_added_to_application_when_submitted(self):
        draft = self.create_standard_draft(self.exporter_user.organisation)

        data = {'id': draft.id}

        response = self.client.post(self.url, data, **self.exporter_headers)
        application = Application.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SiteOnApplication.objects.filter(application=application).count(), 1)
