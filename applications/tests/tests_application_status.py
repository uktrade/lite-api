from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.models import CaseAssignment
from users.models import UserOrganisationRelationship
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token


class ApplicationManageStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.url = reverse("applications:manage_status", kwargs={"pk": self.standard_application.id})

    def test_gov_set_application_status_to_applicant_editing_failure(self):
        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")[0], "Status cannot be set by Gov user.")
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))

    def test_set_application_status_on_application_not_in_users_organisation_failure(self):
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

    def test_exporter_set_application_status_applicant_editing_when_in_editable_status_success(self):
        self.submit_application(self.standard_application)

        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING))

    def test_exporter_set_application_status_withdrawn_when_application_not_terminal_success(self):
        case = self.submit_application(self.standard_application)

        data = {"status": CaseStatusEnum.WITHDRAWN}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.WITHDRAWN))

    @parameterized.expand(
        [case_status for case_status in CaseStatusEnum.terminal_statuses() if case_status != CaseStatusEnum.FINALISED]
    )
    def test_gov_user_set_application_to_terminal_status_removes_case_from_queues_users_success(self, case_status):
        """
        When a case is set to a terminal status, its assigned users, case officer and queues should be removed
        """
        self.submit_application(self.standard_application)
        self.standard_application.case_officer = self.gov_user
        self.standard_application.save()
        self.standard_application.queues.set([self.queue])
        case_assignment = CaseAssignment.objects.create(case=self.standard_application, queue=self.queue)
        case_assignment.users.set([self.gov_user])
        data = {"status": case_status}

        response = self.client.put(self.url, data, **self.gov_headers)
        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status.status, case_status)
        self.assertEqual(self.standard_application.queues.count(), 0)
        self.assertEqual(self.standard_application.case_officer, None)
        self.assertEqual(CaseAssignment.objects.filter(case=self.standard_application).count(), 0)

    def test_exporter_set_application_status_withdrawn_when_application_terminal_failure(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.standard_application.save()

        data = {"status": CaseStatusEnum.WITHDRAWN}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.FINALISED))

    def test_exporter_set_application_status_applicant_editing_when_in_read_only_status_failure(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.UNDER_FINAL_REVIEW)
        self.standard_application.save()

        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.UNDER_FINAL_REVIEW))

    def test_status_cannot_be_set_to_finalised(self):
        data = {"status": CaseStatusEnum.FINALISED}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")[0], "Status cannot be set to finalised.")

    @parameterized.expand(
        [
            status
            for status, value in CaseStatusEnum.choices
            if status not in [CaseStatusEnum.APPLICANT_EDITING, CaseStatusEnum.FINALISED, CaseStatusEnum.WITHDRAWN]
        ]
    )
    def test_exporter_set_application_status_failure(self, new_status):
        """ Test failure in setting application status to any status other than 'Applicant Editing' and 'Withdrawn'
        as an exporter user.
        """
        self.submit_application(self.standard_application)

        data = {"status": new_status}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))

    def test_gov_set_status_to_applicant_editing_failure(self):
        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")[0], "Status cannot be set by Gov user.")
        self.assertEqual(
            self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )

    @parameterized.expand(
        [
            status
            for status, value in CaseStatusEnum.choices
            if status not in [CaseStatusEnum.APPLICANT_EDITING, CaseStatusEnum.FINALISED]
        ]
    )
    def test_gov_set_status_for_all_except_applicant_editing_and_finalised_success(self, case_status):
        data = {"status": case_status}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(case_status))

    def test_gov_set_status_when_they_have_do_not_permission_to_reopen_closed_cases_failure(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.WITHDRAWN)
        self.standard_application.save()

        data = {"status": CaseStatusEnum.REOPENED_FOR_CHANGES}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.WITHDRAWN))

    def test_gov_set_status_when_they_have_permission_to_reopen_closed_cases_success(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.WITHDRAWN)
        self.standard_application.save()

        # Give gov user super used role, to include reopen closed cases permission
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        data = {"status": CaseStatusEnum.REOPENED_FOR_CHANGES}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.standard_application.status, get_case_status_by_status(CaseStatusEnum.REOPENED_FOR_CHANGES)
        )
