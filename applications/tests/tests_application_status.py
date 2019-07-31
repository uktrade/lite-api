from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from static.statuses.enums import CaseStatusEnum
from applications.models import ApplicationDenialReason
from static.statuses.libraries.get_case_status import get_case_status
from test_helpers.clients import DataTestClient


class ApplicationDenialTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application',
                                                                               self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.url = reverse('applications:application', kwargs={'pk': self.application.id})

    @parameterized.expand([
        # Valid reasons and valid reason_details
        [{
            'status': CaseStatusEnum.UNDER_FINAL_REVIEW,
            'reasons': ['1a', '1b', '1c'],
            'reason_details': 'I liked the old way',
        }],
        # Valid reasons and valid missing reason_details
        [{
            'status': CaseStatusEnum.UNDER_FINAL_REVIEW,
            'reasons': ['1a', '1b', '1c'],
        }],
    ])
    def test_set_application_status_successful(self, data):
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.application.refresh_from_db()
        application_denial_reason = ApplicationDenialReason.objects.get(application=self.application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.application.status, get_case_status(CaseStatusEnum.UNDER_FINAL_REVIEW))
        self.assertEqual(application_denial_reason.reason_details,
                         data.get('reason_details'))
        self.assertEqual(application_denial_reason.reasons.all().count(),
                         len(data['reasons']))

    @parameterized.expand([
        # Invalid reasons
        [{
            'status': CaseStatusEnum.UNDER_FINAL_REVIEW,
            'reasons': ['1234', '5678', '8910!'],
            'reason_details': 'I liked the old way',
        }],
        # Empty reasons
        [{
            'status': CaseStatusEnum.UNDER_FINAL_REVIEW,
            'reasons': [],
            'reason_details': 'I liked the old way',
        }],
        # No reasons
        [{
            'status': CaseStatusEnum.UNDER_FINAL_REVIEW,
            'reason_details': 'I liked the old way',
        }],
        # Valid reasons except one
        [{
            'status': CaseStatusEnum.UNDER_FINAL_REVIEW,
            'reasons': ['1a', '1b', '8910!'],
            'reason_details': 'I liked the old way',
        }],
        # Valid reasons but reason_details is too long
        [{
            'status': CaseStatusEnum.UNDER_FINAL_REVIEW,
            'reasons': ['1a', '1b'],
            'reason_details': '🙂' * 2201,
        }],
    ])
    def test_set_application_status_failure(self, data):
        current_status = self.application.status

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.application.status, current_status)
        self.assertEqual(ApplicationDenialReason.objects.filter(application=self.application).count(), 0)
