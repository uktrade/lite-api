from django.urls import reverse
from rest_framework import status

from applications.models import StandardApplication
from test_helpers.clients import DataTestClient


class ApplicationConsigneeTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.url = reverse('applications:application_submit', kwargs={'pk': self.draft.id})

    def test_submit_draft_with_consignee_success(self):
        """
        Given a standard draft has been created with a consignee
        When the draft is submitted
        Then the draft is converted to an application
        """
        response = self.client.put(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(StandardApplication.objects.get().consignee, self.draft.consignee)
