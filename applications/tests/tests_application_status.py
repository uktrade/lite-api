from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.models import ApplicationDenialReason
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status
from test_helpers.clients import DataTestClient


class ApplicationDenialTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_open_application(self.exporter_user.organisation)
        self.url = reverse('applications:application', kwargs={'pk': self.standard_application.id})

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

        self.standard_application.refresh_from_db()
        application_denial_reason = ApplicationDenialReason.objects.get(application=self.standard_application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_from_status(CaseStatusEnum.UNDER_FINAL_REVIEW))
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
        current_status = self.standard_application.status

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.standard_application.status, current_status)
        self.assertEqual(ApplicationDenialReason.objects.filter(application=self.standard_application).count(), 0)
