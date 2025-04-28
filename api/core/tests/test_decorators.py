from api.core.constants import Roles
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import StandardLicenceFactory
from parameterized import parameterized

from django.http import HttpResponse
from django.test import RequestFactory
from rest_framework import status

from api.applications.libraries.case_status_helpers import get_case_statuses
from api.cases.enums import CaseTypeReferenceEnum
from api.core.authentication import ORGANISATION_ID
from api.core.decorators import (
    allowed_application_types,
    application_can_invoke_major_edit,
    application_is_editable,
    application_is_major_editable,
    authorised_govuser_roles,
    authorised_to_view_application,
    licence_is_editable,
)
from lite_content.lite_api import strings
from api.organisations.tests.factories import OrganisationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from api.users.models import ExporterUser, GovUser


class _FakeRequest:
    def __init__(self, user, organisation):
        self.request = RequestFactory().get("")
        self.request.user = user
        self.request.META[ORGANISATION_ID] = str(organisation.id)


class DecoratorTests(DataTestClient):
    def test_allowed_application_types_success(self):
        application = self.create_standard_application_case(self.organisation)

        @allowed_application_types(application_types=[CaseTypeReferenceEnum.SIEL])
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_application_in_state_editable_success(self, editable_status):
        application = self.create_standard_application_case(self.organisation)
        application.status = get_case_status_by_status(editable_status)
        application.save()

        @application_is_editable
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_application_in_state_editable_failure(self):
        application = self.create_standard_application_case(self.organisation)
        application_status = CaseStatusEnum.read_only_statuses()[0]
        application.status = CaseStatus.objects.get(status=application_status)
        application.save()

        @application_is_editable
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            strings.Applications.Generic.INVALID_OPERATION_FOR_READ_ONLY_CASE_ERROR in resp.content.decode("utf-8")
        )

    def test_application_in_state_major_editable_success(self):
        application = self.create_standard_application_case(self.organisation)
        application.status = CaseStatus.objects.get(status=CaseStatusEnum.major_editable_statuses()[0])
        application.save()

        @application_is_major_editable
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_application_in_state_major_editable_failure(self):
        application = self.create_standard_application_case(self.organisation)
        application.status = CaseStatus.objects.get(status=CaseStatusEnum.read_only_statuses()[0])
        application.save()

        @application_is_major_editable
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            strings.Applications.Generic.INVALID_OPERATION_FOR_NON_DRAFT_OR_MAJOR_EDIT_CASE_ERROR
            in resp.content.decode("utf-8")
        )

    @parameterized.expand(CaseStatusEnum.can_invoke_major_edit_statuses)
    def test_application_can_invoke_major_editable_success(self, case_status):
        application = self.create_standard_application_case(self.organisation)
        application.status = CaseStatus.objects.get(status=case_status)
        application.save()

        @application_can_invoke_major_edit
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @parameterized.expand(CaseStatusEnum.can_not_invoke_major_edit_statuses)
    def test_application_can_invoke_major_edit_failure(self, case_status):
        application = self.create_standard_application_case(self.organisation)
        application.status = CaseStatus.objects.get(status=case_status)
        application.save()

        @application_can_invoke_major_edit
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            strings.Applications.Generic.INVALID_OPERATION_FOR_NON_DRAFT_OR_MAJOR_EDIT_CASE_ERROR
            in resp.content.decode("utf-8")
        )

    def test_authorised_to_view_application_exporter_success(self):
        application = self.create_standard_application_case(self.organisation)
        request = _FakeRequest(self.exporter_user, self.organisation)

        @authorised_to_view_application(ExporterUser)
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=request, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_authorised_to_view_application_gov_success(self):
        application = self.create_standard_application_case(self.organisation)
        request = _FakeRequest(self.gov_user, self.organisation)

        @authorised_to_view_application(GovUser)
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=request, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_authorised_to_view_application_wrong_user_type_failure(self):
        application = self.create_standard_application_case(self.organisation)
        request = _FakeRequest(self.exporter_user, self.organisation)

        @authorised_to_view_application(GovUser)
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=request, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("You are not authorised to perform this operation" in resp.content.decode("utf-8"))

    def test_authorised_to_view_application_wrong_organisation_failure(self):
        application = self.create_standard_application_case(self.organisation)
        organisation = OrganisationFactory()
        request = _FakeRequest(self.exporter_user, organisation)

        @authorised_to_view_application(ExporterUser)
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=request, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            "You can only perform this operation on an application that has been opened within your organisation"
            in resp.content.decode("utf-8")
        )

    def test_authorised_roles_govuser_success(self):
        request = _FakeRequest(self.gov_user, self.organisation)

        @authorised_govuser_roles([Roles.INTERNAL_DEFAULT_ROLE_ID])
        def a_view(request, *args, **kwargs):
            return HttpResponse()

    def test_authorised_roles_exporter_failure(self):
        request = _FakeRequest(self.exporter_user, self.organisation)

        @authorised_govuser_roles([Roles.INTERNAL_DEFAULT_ROLE_ID])
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=request)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("You are not authorised to perform this operation" in resp.content.decode("utf-8"))

    def test_authorised_roles_govuser_role_failure(self):
        request = _FakeRequest(self.gov_user, self.organisation)

        @authorised_govuser_roles([Roles.INTERNAL_LU_SENIOR_MANAGER_ROLE_ID])
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=request)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("The user must be in a specific role to perform this action." in resp.content.decode("utf-8"))

    @parameterized.expand(
        [
            [LicenceStatus.ISSUED],
            [LicenceStatus.REINSTATED],
            [LicenceStatus.SUSPENDED],
        ]
    )
    def test_licence_is_editable_success(self, licence_status):
        application = self.create_standard_application_case(self.organisation)
        licence = StandardLicenceFactory(case=application, status=licence_status)
        application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        application.save()

        request = _FakeRequest(self.exporter_user, self.organisation)

        @licence_is_editable()
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=request, pk=licence.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @parameterized.expand(
        [
            [LicenceStatus.ISSUED, CaseStatusEnum.DRAFT, "To edit a licence the case must be in a finalised state."],
            [
                LicenceStatus.REINSTATED,
                CaseStatusEnum.INITIAL_CHECKS,
                "To edit a licence the case must be in a finalised state.",
            ],
            [
                LicenceStatus.SUSPENDED,
                CaseStatusEnum.RESUBMITTED,
                "To edit a licence the case must be in a finalised state.",
            ],
            [LicenceStatus.REVOKED, CaseStatusEnum.FINALISED, "The licence status is not editable."],
            [LicenceStatus.SURRENDERED, CaseStatusEnum.FINALISED, "The licence status is not editable."],
            [LicenceStatus.EXHAUSTED, CaseStatusEnum.FINALISED, "The licence status is not editable."],
            [LicenceStatus.EXPIRED, CaseStatusEnum.FINALISED, "The licence status is not editable."],
            [LicenceStatus.DRAFT, CaseStatusEnum.FINALISED, "The licence status is not editable."],
            [LicenceStatus.CANCELLED, CaseStatusEnum.FINALISED, "The licence status is not editable."],
        ]
    )
    def test_licence_is_editable_failure(self, licence_status, case_status, error_msg):
        application = self.create_standard_application_case(self.organisation)
        licence = StandardLicenceFactory(case=application, status=licence_status)
        application.status = get_case_status_by_status(case_status)
        application.save()

        request = _FakeRequest(self.exporter_user, self.organisation)

        @licence_is_editable()
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=request, pk=licence.pk)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(error_msg in resp.content.decode("utf-8"))
