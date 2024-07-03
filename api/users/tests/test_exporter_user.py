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
            *[(terminal_status, CaseStatusEnum.WITHDRAWN) for terminal_status in CaseStatusEnum.terminal_statuses()],
            *[
                (status, CaseStatusEnum.SURRENDERED)
                for status in CaseStatusEnum.all()
                if status != CaseStatusEnum.FINALISED
            ],
            *[
                (status, CaseStatusEnum.APPLICANT_EDITING)
                for status in CaseStatusEnum.all()
                if status
                not in [
                    *CaseStatusEnum.can_invoke_major_edit_statuses(),
                    CaseStatusEnum.DRAFT,
                    CaseStatusEnum.APPLICANT_EDITING,
                ]
            ],
            *[
                (status, CaseStatusEnum.SUBMITTED)
                for status in CaseStatusEnum.all()
                if status not in CaseStatusEnum.writeable_statuses()
            ],
            *[
                (CaseStatusEnum.SUBMITTED, status)
                for status in CaseStatusEnum.all()
                if status != CaseStatusEnum.APPLICANT_EDITING
            ],
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
