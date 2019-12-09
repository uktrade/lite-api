import json

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.libraries.case_status_helpers import get_case_statuses
from applications.models import ApplicationDenialReason
from users.models import UserOrganisationRelationship
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token


class ApplicationDenialTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.url = reverse("applications:manage_status", kwargs={"pk": self.standard_application.id})

    @parameterized.expand(
        [
            # Valid reasons and valid reason_details
            [
                {
                    "status": CaseStatusEnum.UNDER_FINAL_REVIEW,
                    "reasons": ["1a", "1b", "1c"],
                    "reason_details": "I liked the old way",
                }
            ],
            # Valid reasons and valid missing reason_details
            [{"status": CaseStatusEnum.UNDER_FINAL_REVIEW, "reasons": ["1a", "1b", "1c"],}],
        ]
    )
    def test_set_application_status_successful(self, data):
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        application_denial_reason = ApplicationDenialReason.objects.get(application=self.standard_application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.standard_application.status, get_case_status_by_status(CaseStatusEnum.UNDER_FINAL_REVIEW),
        )
        self.assertEqual(application_denial_reason.reason_details, data.get("reason_details"))
        self.assertEqual(application_denial_reason.reasons.all().count(), len(data["reasons"]))

    @parameterized.expand(
        [
            # Invalid reasons
            [
                {
                    "status": CaseStatusEnum.UNDER_FINAL_REVIEW,
                    "reasons": ["1234", "5678", "8910!"],
                    "reason_details": "I liked the old way",
                }
            ],
            # Empty reasons
            [{"status": CaseStatusEnum.UNDER_FINAL_REVIEW, "reasons": [], "reason_details": "I liked the old way",}],
            # No reasons
            [{"status": CaseStatusEnum.UNDER_FINAL_REVIEW, "reason_details": "I liked the old way",}],
            # Valid reasons except one
            [
                {
                    "status": CaseStatusEnum.UNDER_FINAL_REVIEW,
                    "reasons": ["1a", "1b", "8910!"],
                    "reason_details": "I liked the old way",
                }
            ],
            # Valid reasons but reason_details is too long
            [{"status": CaseStatusEnum.UNDER_FINAL_REVIEW, "reasons": ["1a", "1b"], "reason_details": "🙂" * 2201,}],
        ]
    )
    def test_gov_set_application_status_failure(self, data):
        current_status = self.standard_application.status

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.standard_application.status, current_status)
        self.assertEqual(
            ApplicationDenialReason.objects.filter(application=self.standard_application).count(), 0,
        )

    def test_gov_set_application_status_to_applicant_editing_failure(self):
        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            json.loads(response.content).get("errors")[0],
            'Setting application status to "applicant_editing" is not allowed for GovUsers.',
        )
        self.assertEqual(
            self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )

    def test_set_application_status_on_application_not_in_users_organisation_failure(self,):
        self.submit_application(self.standard_application)
        other_organisation, _ = self.create_organisation_with_exporter_user()
        data = {"status": "Invalid status"}
        permission_denied_user = UserOrganisationRelationship.objects.get(organisation=other_organisation).user
        permission_denied_user_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(permission_denied_user),
            "HTTP_ORGANISATION_ID": other_organisation.id,
        }

        response = self.client.put(self.url, data=data, **permission_denied_user_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_exporter_set_application_status_applicant_editing_when_in_editable_status_success(self, editable_status):
        self.standard_application.status = get_case_status_by_status(editable_status)
        self.standard_application.save()

        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING))

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_exporter_set_application_status_applicant_editing_when_in_read_only_status_failure(self, read_only_status):
        self.standard_application.status = get_case_status_by_status(read_only_status)
        self.standard_application.save()

        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(read_only_status))

    @parameterized.expand(
        [
            status
            for status, value in CaseStatusEnum.choices
            if status != CaseStatusEnum.APPLICANT_EDITING and status != CaseStatusEnum.FINALISED
        ]
    )
    def test_exporter_set_application_status_failure(self, editable_status):
        """ Test failure in setting application status to any status other than 'Applicant Editing'
        as an exporter user.

        """
        self.submit_application(self.standard_application)

        data = {"status": editable_status}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))
