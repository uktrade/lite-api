from django.urls import reverse
from parameterized import parameterized
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
        application_denial_reason = ApplicationDenialReason.objects.get(application=self.application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.application.status, ApplicationStatus.DECLINED)
        self.assertEqual(application_denial_reason.reasoning,
                         data['reasoning'])
        self.assertEqual(application_denial_reason.reasons.all().count(),
                         len(data['reasons']))

    @parameterized.expand([
        [{
            'status': ApplicationStatus.DECLINED,
            'reasons': ['1234', '5678', '8910!'],
            'reasoning': 'I liked the old way',
        }],
        [{
            'status': ApplicationStatus.DECLINED,
            'reasons': ['1a', '1b', '8910!'],
            'reasoning': 'I liked the old way',
        }],
        [{
            'status': ApplicationStatus.DECLINED,
            'reasons': ['1a', '1b'],
            'reasoning': '🙂' * 2201,
        }],
    ])
    def test_set_application_status_failure(self, data):
        current_status = self.application.status

        response = self.client.put(self.url, data=data)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.application.status, current_status)
        self.assertEqual(ApplicationDenialReason.objects.filter(application=self.application).count(), 0)
