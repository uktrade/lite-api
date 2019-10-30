import json

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.models import ApplicationDenialReason
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token
from users.models import UserOrganisationRelationship


class ApplicationDenialTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.url = reverse('applications:manage_status', kwargs={'pk': self.standard_application.id})

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
        self.assertEqual(self.standard_application.status,
                         get_case_status_by_status(CaseStatusEnum.UNDER_FINAL_REVIEW))
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

    def test_exp_set_application_status_to_applicant_editing_when_previously_submitted_success(self):
        data = {'status': CaseStatusEnum.APPLICANT_EDITING}
        previous_submitted_at = self.standard_application.submitted_at

        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status,
                         get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING))
        self.assertEqual(self.standard_application.submitted_at, previous_submitted_at)

    def test_exp_set_application_status_to_applicant_editing_when_not_previously_submitted_failure(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.MORE_INFORMATION_REQUIRED)
        self.standard_application.save()

        data = {'status': CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content).get('errors')[0],
                         'Setting application status to "applicant_editing" when application status is '
                         '"more_information_required" is not allowed.')
        self.assertEqual(self.standard_application.status,
                         get_case_status_by_status(CaseStatusEnum.MORE_INFORMATION_REQUIRED))

    def test_gov_set_application_status_to_applicant_editing_failure(self):
        data = {'status': CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content).get('errors')[0],
                         'Setting application status to "applicant_editing" is not allowed for GovUsers.')
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))

    def test_gov_set_application_status_when_previously_applicant_editing_failure(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.standard_application.save()

        data = {'status': CaseStatusEnum.MORE_INFORMATION_REQUIRED}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content).get('errors')[0],
                         'Setting application status when its existing status is "applicant_editing"'
                         ' is not allowed for GovUsers.')
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING))

    def test_set_application_status_to_submitted_failure(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.standard_application.save()

        data = {'status': CaseStatusEnum.SUBMITTED}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content).get('errors')[0],
                         'Setting application status to "submitted" is not allowed.')
        self.assertEqual(self.standard_application.status,
                         get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING))

    def test_set_application_status_to_invalid_status_failure(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        self.standard_application.save()

        data = {'status': 'something_stupid'}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))

    def test_set_application_status_on_application_not_in_users_organisation_failure(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        self.standard_application.save()

        other_organisation = self.create_organisation_with_exporter_user()
        permission_denied_user = UserOrganisationRelationship.objects.get(organisation=other_organisation).user
        permission_denied_user_headers = {
            'HTTP_EXPORTER_USER_TOKEN': user_to_token(permission_denied_user),
            'HTTP_ORGANISATION_ID': other_organisation.id
        }

        data = {'status': 'something_stupid'}
        response = self.client.put(self.url, data=data, **permission_denied_user_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))