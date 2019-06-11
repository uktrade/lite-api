from django.urls import reverse
from rest_framework import status

from applications.enums import ApplicationStatus
from test_helpers.clients import DataTestClient


class AuditTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application',
                                                                               self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.url = reverse('audit:audit_detail', kwargs={'type': 'applications', 'pk': self.application.id})

    def test_view_audit_history(self):
        """
        Submit an application and check that there is an audit trail
        """
        response = self.client.get(self.url)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['changes']), 1)

        # Update the status and and check that the audit trail is updated
        data = {
            'status': ApplicationStatus.APPROVED,
        }

        self.client.put(reverse('applications:application', kwargs={'pk': self.application.id}), data=data)

        # Validate that there are now two objects in changes
        response = self.client.get(self.url)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['changes']), 2)
