from unittest import mock

from django.conf import settings
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.models import CaseAssignment
from gov_notify.enums import TemplateType
from licences.enums import LicenceStatus
from lite_content.lite_api import strings
from users.models import UserOrganisationRelationship
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token


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
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(permission_denied_user),
            "HTTP_ORGANISATION_ID": str(other_organisation.id),
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

    @mock.patch("gov_notify.service.client")
    def test_exporter_set_application_status_withdrawn_when_application_not_terminal_success(self, mock_notify_client):
        self.submit_application(self.standard_application)

        data = {"status": CaseStatusEnum.WITHDRAWN}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.WITHDRAWN))
        mock_notify_client.send_email.assert_called_with(
            email_address=self.standard_application.submitted_by.email,
            template_id=TemplateType.APPLICATION_STATUS.template_id,
            data={
                "case_reference": self.standard_application.reference_code,
                "application_reference": self.standard_application.name,
                "link": f"{settings.EXPORTER_BASE_URL}/applications/{self.standard_application.pk}",
            },
        )

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

        with mock.patch("gov_notify.service.client") as mock_notify_client:
            response = self.client.put(self.url, data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status.status, case_status)
        self.assertEqual(self.standard_application.queues.count(), 0)
        self.assertEqual(self.standard_application.case_officer, None)
        self.assertEqual(CaseAssignment.objects.filter(case=self.standard_application).count(), 0)
        mock_notify_client.send_email.assert_called_with(
            email_address=self.standard_application.submitted_by.email,
            template_id=TemplateType.APPLICATION_STATUS.template_id,
            data={
                "case_reference": self.standard_application.reference_code,
                "application_reference": self.standard_application.name,
                "link": f"{settings.EXPORTER_BASE_URL}/applications/{self.standard_application.pk}",
            },
        )

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

    @mock.patch("gov_notify.service.client")
    def test_exporter_set_application_status_surrendered_success(self, mock_notify_client):
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.standard_application.save()
        self.create_licence(self.standard_application, status=LicenceStatus.ISSUED)
        surrendered_status = get_case_status_by_status("surrendered")

        data = {"status": CaseStatusEnum.SURRENDERED}
        response = self.client.put(self.url, data=data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data["status"],
            {"key": surrendered_status.status, "value": CaseStatusEnum.get_text(surrendered_status.status)},
        )
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SURRENDERED))
        mock_notify_client.send_email.assert_called_with(
            email_address=self.standard_application.submitted_by.email,
            template_id=TemplateType.APPLICATION_STATUS.template_id,
            data={
                "case_reference": self.standard_application.reference_code,
                "application_reference": self.standard_application.name,
                "link": f"{settings.EXPORTER_BASE_URL}/applications/{self.standard_application.pk}",
            },
        )

    def test_exporter_set_application_status_surrendered_no_licence_failure(self):
        """ Test failure in exporter user setting a case status to surrendered when the case
        does not have a licence duration
        """
        self.standard_application.licences.update(duration=None)
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.standard_application.save()

        data = {"status": CaseStatusEnum.SURRENDERED}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": [strings.Applications.Generic.Finalise.Error.SURRENDER]})
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.FINALISED))

    def test_exporter_set_application_status_surrendered_not_finalised_failure(self):
        """ Test failure in exporter user setting a case status to surrendered when the case was not
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
            self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )

    @parameterized.expand(
        [
            status
            for status, value in CaseStatusEnum.choices
            if status
            not in [
                CaseStatusEnum.APPLICANT_EDITING,
                CaseStatusEnum.FINALISED,
                CaseStatusEnum.SURRENDERED,
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

        with mock.patch("gov_notify.service.client") as mock_notify_client:
            response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(case_status))

        if CaseStatusEnum.is_terminal(case_status):
            mock_notify_client.send_email.assert_called_with(
                email_address=self.standard_application.submitted_by.email,
                template_id=TemplateType.APPLICATION_STATUS.template_id,
                data={
                    "case_reference": self.standard_application.reference_code,
                    "application_reference": self.standard_application.name,
                    "link": f"{settings.EXPORTER_BASE_URL}/applications/{self.standard_application.pk}",
                },
            )

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
        self.assertEqual(self.standard_application.queues.count(), 1)
        self.assertEqual(self.standard_application.queues.first().id, routing_queue.id)

    def test_gov_user_set_hmrc_status_closed_success(self):
        self.hmrc_query = self.create_hmrc_query(self.organisation)
        self.submit_application(self.hmrc_query)

        data = {"status": CaseStatusEnum.CLOSED}
        url = reverse("applications:manage_status", kwargs={"pk": self.hmrc_query.id})
        response = self.client.put(url, data=data, **self.gov_headers)

        self.hmrc_query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.hmrc_query.status, get_case_status_by_status(CaseStatusEnum.CLOSED))

    def test_gov_user_set_hmrc_invalid_status_failure(self):
        self.hmrc_query = self.create_hmrc_query(self.organisation)
        self.submit_application(self.hmrc_query)

        # HMRC case status can only be CLOSED, SUBMITTED or RESUBMITTED
        data = {"status": CaseStatusEnum.WITHDRAWN}
        url = reverse("applications:manage_status", kwargs={"pk": self.hmrc_query.id})
        response = self.client.put(url, data=data, **self.gov_headers)

        self.hmrc_query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")["status"][0], strings.Statuses.BAD_STATUS)
        self.assertEqual(
            self.standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )
