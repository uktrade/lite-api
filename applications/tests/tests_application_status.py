from django.urls import reverse
from rest_framework import status

from applications.enums import ApplicationStatus
from applications.models import ApplicationDenialReason
from test_helpers.clients import DataTestClient


class ApplicationDenialTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application',
                                                                               self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.url = reverse('applications:application', kwargs={'pk': self.application.id})

    def test_set_application_status_successful(self):
        data = {
            'status': ApplicationStatus.DECLINED,
            'reasons': ['1a', '1b', '1c'],
            'reasoning': 'I liked the old way',
        }

        response = self.client.put(self.url, data=data)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.application.status, ApplicationStatus.DECLINED)
        self.assertEqual(ApplicationDenialReason.objects.get(application=self.application).reasoning,
                         data['reasoning'])
        self.assertEqual(len(ApplicationDenialReason.objects.get(application=self.application).reasons),
                         len(data['reasons']))
