from unittest import mock

from django.conf import settings
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.audit_trail.models import AuditType, Audit
from api.core.constants import GovPermissions
from api.cases.models import CaseAssignment
from api.licences.enums import LicenceStatus
from api.teams.models import Team
from api.users.models import UserOrganisationRelationship, Permission
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from api.users.libraries.user_to_token import user_to_token

from lite_content.lite_api import strings
from lite_routing.routing_rules_internal.enums import TeamIdEnum


class ApplicationManageStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.url = reverse("applications:manage_status", kwargs={"pk": self.standard_application.id})

    def test_gov_set_application_status_to_applicant_editing_failure(self):
        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")[0], strings.Applications.Generic.Finalise.Error.GOV_SET_STATUS)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))

    def test_set_application_status_on_application_not_in_users_organisation_failure(self):
        self.submit_application(self.standard_application)
        other_organisation, _ = self.create_organisation_with_exporter_user()
        data = {"status": "Invalid status"}
        permission_denied_user = UserOrganisationRelationship.objects.get(organisation=other_organisation).user
        permission_denied_user_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(permission_denied_user.baseuser_ptr),
            "HTTP_ORGANISATION_ID": str(other_organisation.id),
        }

        response = self.client.put(self.url, data=data, **permission_denied_user_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))

    @mock.patch("api.applications.views.applications.notify_exporter_case_opened_for_editing")
    def test_exporter_set_application_status_applicant_editing_when_in_editable_status_success(self, mock_notify):
        self.submit_application(self.standard_application)

        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING))
        audit_event = Audit.objects.first()
        self.assertEqual(audit_event.verb, AuditType.UPDATED_STATUS)
        self.assertEqual(
            audit_event.payload, {"status": {"new": CaseStatusEnum.APPLICANT_EDITING, "old": CaseStatusEnum.SUBMITTED}}
        )
        mock_notify.assert_called_with(self.standard_application)

    def test_exporter_set_application_status_withdrawn_when_application_not_terminal_success(self):
        self.submit_application(self.standard_application)

        data = {"status": CaseStatusEnum.WITHDRAWN}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.WITHDRAWN))

    @parameterized.expand(
        [
            case_status
            for case_status in CaseStatusEnum.terminal_statuses()
            if case_status not in [CaseStatusEnum.FINALISED, CaseStatusEnum.SURRENDERED]
        ]
    )
    def test_gov_user_set_application_to_terminal_status_removes_case_from_queues_users_success(self, case_status):
        """
        When a case is set to a terminal status, its assigned users, case officer and queues should be removed
        """
        self.submit_application(self.standard_application)
        self.standard_application.case_officer = self.gov_user
        self.standard_application.save()
        self.standard_application.queues.set([self.queue])
        case_assignment = CaseAssignment.objects.create(
            case=self.standard_application, queue=self.queue, user=self.gov_user
        )
        if case_status == CaseStatusEnum.REVOKED:
            self.standard_application.licences.add(
                self.create_licence(self.standard_application, status=LicenceStatus.ISSUED)
            )

        data = {"status": case_status}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status.status, case_status)
        self.assertEqual(self.standard_application.queues.count(), 0)
        self.assertEqual(self.standard_application.case_officer, None)
        self.assertEqual(CaseAssignment.objects.filter(case=self.standard_application).count(), 0)

    @parameterized.expand(
        [
            (
                CaseStatusEnum.SUSPENDED,
                LicenceStatus.SUSPENDED,
            ),
            (
                CaseStatusEnum.SURRENDERED,
                LicenceStatus.SURRENDERED,
            ),
            (
                CaseStatusEnum.REVOKED,
                LicenceStatus.REVOKED,
            ),
        ]
    )
    def test_certain_case_statuses_changes_licence_status(self, case_status, licence_status):
        licence = self.create_licence(self.standard_application, status=LicenceStatus.ISSUED)

        data = {"status": case_status}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        licence.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["status"]["key"], case_status)
        self.assertEqual(self.standard_application.status.status, case_status)
        self.assertEqual(licence.status, licence_status)

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

    @parameterized.expand(
        [
            status
            for status, value in CaseStatusEnum.get_choices()
            if status not in [CaseStatusEnum.APPLICANT_EDITING, CaseStatusEnum.FINALISED, CaseStatusEnum.WITHDRAWN]
        ]
    )
    def test_exporter_set_application_status_failure(self, new_status):
        """Test failure in setting application status to any status other than 'Applicant Editing' and 'Withdrawn'
        as an exporter user.
        """
        self.submit_application(self.standard_application)

        data = {"status": new_status}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))

    def test_exporter_set_application_status_surrendered_success(self):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.standard_application.save()
        self.create_licence(self.standard_application, status=LicenceStatus.ISSUED)
        surrendered_status = get_case_status_by_status("surrendered")

        data = {"status": CaseStatusEnum.SURRENDERED}
        response = self.client.put(self.url, data=data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data["status"].pop("id", None)
        self.assertEqual(
            response_data["status"],
            {"key": surrendered_status.status, "value": CaseStatusEnum.get_text(surrendered_status.status)},
        )
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SURRENDERED))

    def test_exporter_set_application_status_surrendered_no_licence_failure(self):
        """Test failure in exporter user setting a case status to surrendered when the case
        does not have a licence duration
        """
        self.standard_application.licences.update(duration=None)
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.standard_application.save()

        data = {"status": CaseStatusEnum.SURRENDERED}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(), {"errors": {"status": [strings.Applications.Generic.Finalise.Error.SURRENDER]}}
        )
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.FINALISED))

    def test_exporter_set_application_status_surrendered_not_finalised_failure(self):
        """Test failure in exporter user setting a case status to surrendered when the case was not
        previously finalised.
        """
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        self.standard_application.save()

        data = {"status": CaseStatusEnum.SURRENDERED}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": [strings.Applications.Generic.Finalise.Error.EXPORTER_SET_STATUS]})
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED))

    def test_exporter_cannot_set_status_to_finalised(self):
        data = {"status": CaseStatusEnum.FINALISED}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")[0], strings.Applications.Generic.Finalise.Error.SET_FINALISED)

    def test_gov_set_status_to_applicant_editing_failure(self):
        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")[0], strings.Applications.Generic.Finalise.Error.GOV_SET_STATUS)
        self.assertEqual(
            self.standard_application.status,
            get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )

    @parameterized.expand(
        [
            status
            for status, value in CaseStatusEnum.get_choices()
            if status
            not in [
                CaseStatusEnum.APPLICANT_EDITING,
                CaseStatusEnum.FINALISED,
                CaseStatusEnum.SURRENDERED,
                CaseStatusEnum.SUSPENDED,
                CaseStatusEnum.REOPENED_FOR_CHANGES,
            ]
        ]
    )
    def test_gov_set_status_for_all_except_applicant_editing_and_finalised_success(self, case_status):
        if case_status == CaseStatusEnum.REVOKED:
            self.standard_application.licences.add(
                self.create_licence(self.standard_application, status=LicenceStatus.ISSUED)
            )

        data = {"status": case_status}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(case_status))

    @parameterized.expand([CaseStatusEnum.REOPENED_FOR_CHANGES, CaseStatusEnum.REOPENED_DUE_TO_ORG_CHANGES])
    def test_gov_set_status_when_they_have_do_not_permission_to_reopen_closed_cases_failure(self, reopened_status):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.WITHDRAWN)
        self.standard_application.save()

        data = {"status": reopened_status}
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

    def test_case_routing_automation(self):
        routing_queue = self.create_queue("new queue", self.team)
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=routing_queue.id,
            tier=3,
            status_id=get_case_status_by_status(CaseStatusEnum.UNDER_REVIEW).id,
            additional_rules=[],
        )
        self.assertNotEqual(self.standard_application.status.status, CaseStatusEnum.UNDER_REVIEW)

        data = {"status": CaseStatusEnum.UNDER_REVIEW}

        response = self.client.put(self.url, data, **self.gov_headers)
        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status.status, CaseStatusEnum.UNDER_REVIEW)
        self.assertEqual(self.standard_application.queues.count(), 2)
        self.assertEqual(
            sorted([queue.name for queue in self.standard_application.queues.all()]),
            ["Licensing Unit Pre-circulation Cases to Review", "new queue"],
        )

    def test_gov_user_set_hmrc_status_closed_success(self):
        self.hmrc_query = self.create_hmrc_query(self.organisation)
        self.submit_application(self.hmrc_query)

        data = {"status": CaseStatusEnum.CLOSED}
        url = reverse("applications:manage_status", kwargs={"pk": self.hmrc_query.id})
        response = self.client.put(url, data=data, **self.gov_headers)

        self.hmrc_query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.hmrc_query.status, get_case_status_by_status(CaseStatusEnum.CLOSED))

    @parameterized.expand(
        [
            (
                TeamIdEnum.TECHNICAL_ASSESSMENT_UNIT,
                [],
                CaseStatusEnum.INITIAL_CHECKS,
                CaseStatusEnum.INITIAL_CHECKS,
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                TeamIdEnum.TECHNICAL_ASSESSMENT_UNIT,
                [GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name],
                CaseStatusEnum.INITIAL_CHECKS,
                CaseStatusEnum.INITIAL_CHECKS,
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                TeamIdEnum.LICENSING_UNIT,
                [],
                CaseStatusEnum.UNDER_FINAL_REVIEW,
                CaseStatusEnum.UNDER_FINAL_REVIEW,
                status.HTTP_403_FORBIDDEN,
            ),
            (
                TeamIdEnum.LICENSING_UNIT,
                [GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name],
                CaseStatusEnum.UNDER_FINAL_REVIEW,
                CaseStatusEnum.FINALISED,
                status.HTTP_200_OK,
            ),
        ]
    )
    def test_gov_user_set_status_to_finalised(
        self, team_id, permissions, initial_status, expected_status, expected_status_code
    ):
        self.standard_application.status = get_case_status_by_status(initial_status)
        self.standard_application.save()
        self.assertEqual(self.standard_application.status, get_case_status_by_status(initial_status))

        self.gov_user.team = Team.objects.get(id=team_id)
        self.gov_user.save()

        self.gov_user.role.permissions.add(*Permission.objects.filter(id__in=permissions))

        data = {"status": CaseStatusEnum.FINALISED}

        response = self.client.put(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, expected_status_code)

        self.standard_application.refresh_from_db()
        self.assertEqual(self.standard_application.status, get_case_status_by_status(expected_status))
