import json
import uuid

from parameterized import parameterized

from django.http import JsonResponse
from django.test import RequestFactory

from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from test_helpers.clients import DataTestClient

from lite_content.lite_api import strings

from api.applications.tests.factories import StandardApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.users.tests.factories import (
    ExporterUserFactory,
    UserOrganisationRelationshipFactory,
)


class ExporterUserTests(DataTestClient):
    def test_is_in_organisation(self):
        self.assertTrue(self.exporter_user.is_in_organisation(self.organisation))

        another_organisation = self.create_organisation_with_exporter_user()[0]
        self.assertFalse(self.exporter_user.is_in_organisation(another_organisation))

    def test_can_set_status_different_organisation(self):
        exporter_user = ExporterUserFactory()
        UserOrganisationRelationshipFactory(
            organisation=self.organisation,
            user=exporter_user,
        )

        factory = RequestFactory()
        request = factory.get(
            "/",
            headers={"ORGANISATION_ID": str(uuid.uuid4())},
        )

        application = StandardApplicationFactory()

        data = {
            "status": CaseStatusEnum.APPLICANT_EDITING,
        }

        with self.assertRaises(PermissionDenied):
            exporter_user.can_set_status(request, application, data)

    def test_can_set_status_same_organisation(self):
        exporter_user = ExporterUserFactory()
        UserOrganisationRelationshipFactory(
            organisation=self.organisation,
            user=exporter_user,
        )

        factory = RequestFactory()
        request = factory.get(
            "/",
            headers={"ORGANISATION_ID": str(self.organisation.pk)},
        )

        application = StandardApplicationFactory(
            organisation=self.organisation,
        )

        data = {
            "status": CaseStatusEnum.APPLICANT_EDITING,
        }

        self.assertIsNone(exporter_user.can_set_status(request, application, data))

    def test_can_set_status_finalised_status(self):
        exporter_user = ExporterUserFactory()
        UserOrganisationRelationshipFactory(
            organisation=self.organisation,
            user=exporter_user,
        )

        factory = RequestFactory()
        request = factory.get(
            "/",
            headers={"ORGANISATION_ID": str(self.organisation.pk)},
        )

        application = StandardApplicationFactory(
            organisation=self.organisation,
        )

        data = {
            "status": CaseStatusEnum.FINALISED,
        }

        response = exporter_user.can_set_status(request, application, data)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            json.loads(response.content), {"errors": [strings.Applications.Generic.Finalise.Error.SET_FINALISED]}
        )

    @parameterized.expand(
        [
            # *[(terminal_status, CaseStatusEnum.WITHDRAWN) for terminal_status in CaseStatusEnum.terminal_statuses()],
            # *[(status, CaseStatusEnum.SURRENDERED) for status in CaseStatusEnum.all() if status != CaseStatusEnum.FINALISED],
            *[
                (status, CaseStatusEnum.APPLICANT_EDITING)
                for status in CaseStatusEnum.all()
                if status not in CaseStatusEnum.can_invoke_major_edit_statuses()
            ],
            # (CaseStatusEnum.APPEAL_FINAL_REVIEW, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.APPEAL_REVIEW, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.CHANGE_INTIAL_REVIEW, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.CHANGE_UNDER_FINAL_REVIEW, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.CHANGE_UNDER_REVIEW, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.CLC, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.OPEN, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.UNDER_INTERNAL_REVIEW, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.RETURN_TO_INSPECTOR, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.AWAITING_EXPORTER_RESPONSE, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.CLOSED, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.DEREGISTERED, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.FINALISED, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.PV, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.REGISTERED, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.REOPENED_DUE_TO_ORG_CHANGES, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.RESUBMITTED, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.REVOKED, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.OGD_ADVICE, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.SURRENDERED, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.SUSPENDED, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.UNDER_APPEAL, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.UNDER_ECJU_REVIEW, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.UNDER_FINAL_REVIEW, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.WITHDRAWN, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.OGD_CONSOLIDATION, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.FINAL_REVIEW_SECOND_COUNTERSIGN, CaseStatusEnum.APPLICANT_EDITING),
            # (CaseStatusEnum.SUPERSEDED_BY_AMENDMENT, CaseStatusEnum.APPLICANT_EDITING),
            (CaseStatusEnum.APPEAL_FINAL_REVIEW, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.APPEAL_REVIEW, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.APPLICANT_EDITING, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.CHANGE_INTIAL_REVIEW, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.CHANGE_UNDER_FINAL_REVIEW, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.CHANGE_UNDER_REVIEW, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.CLC, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.OPEN, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.UNDER_INTERNAL_REVIEW, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.RETURN_TO_INSPECTOR, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.AWAITING_EXPORTER_RESPONSE, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.CLOSED, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.DEREGISTERED, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.FINALISED, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.INITIAL_CHECKS, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.PV, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.REGISTERED, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.REOPENED_FOR_CHANGES, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.REOPENED_DUE_TO_ORG_CHANGES, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.RESUBMITTED, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.REVOKED, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.OGD_ADVICE, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.SURRENDERED, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.SUSPENDED, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.UNDER_APPEAL, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.UNDER_ECJU_REVIEW, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.UNDER_FINAL_REVIEW, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.WITHDRAWN, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.OGD_CONSOLIDATION, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.FINAL_REVIEW_SECOND_COUNTERSIGN, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.SUPERSEDED_BY_AMENDMENT, CaseStatusEnum.SUBMITTED),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.APPEAL_FINAL_REVIEW),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.APPEAL_REVIEW),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.CHANGE_INTIAL_REVIEW),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.CHANGE_UNDER_FINAL_REVIEW),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.CHANGE_UNDER_REVIEW),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.CLC),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.OPEN),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.UNDER_INTERNAL_REVIEW),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.RETURN_TO_INSPECTOR),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.AWAITING_EXPORTER_RESPONSE),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.CLOSED),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.DEREGISTERED),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.INITIAL_CHECKS),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.PV),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.REGISTERED),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.REOPENED_FOR_CHANGES),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.REOPENED_DUE_TO_ORG_CHANGES),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.RESUBMITTED),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.REVOKED),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.OGD_ADVICE),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.SURRENDERED),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.SUSPENDED),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.UNDER_APPEAL),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.UNDER_ECJU_REVIEW),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.UNDER_FINAL_REVIEW),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.OGD_CONSOLIDATION),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.FINAL_REVIEW_SECOND_COUNTERSIGN),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.SUPERSEDED_BY_AMENDMENT),
        ]
    )
    def test_can_set_status_with_status_deny_setting(self, original_status, new_status):
        exporter_user = ExporterUserFactory()
        UserOrganisationRelationshipFactory(
            organisation=self.organisation,
            user=exporter_user,
        )

        factory = RequestFactory()
        request = factory.get(
            "/",
            headers={"ORGANISATION_ID": str(self.organisation.pk)},
        )

        application = StandardApplicationFactory(
            organisation=self.organisation,
            status=CaseStatus.objects.get(status=original_status),
        )

        data = {
            "status": new_status,
        }

        response = exporter_user.can_set_status(request, application, data)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            json.loads(response.content), {"errors": [strings.Applications.Generic.Finalise.Error.EXPORTER_SET_STATUS]}
        )
