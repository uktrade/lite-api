from django.http import HttpResponse
from django.test import RequestFactory
from rest_framework import status

from cases.enums import CaseTypeSubTypeEnum
from api.conf.authentication import ORGANISATION_ID
from api.conf.decorators import allowed_application_types, application_in_state, authorised_to_view_application
from lite_content.lite_api import strings
from api.organisations.tests.factories import OrganisationFactory
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from users.models import ExporterUser, GovUser


class _FakeRequest:
    def __init__(self, user, organisation):
        self.request = RequestFactory().get("")
        self.request.user = user
        self.request.META[ORGANISATION_ID] = str(organisation.id)


class DecoratorTests(DataTestClient):
    def test_allowed_application_types_success(self):
        application = self.create_standard_application_case(self.organisation)

        @allowed_application_types(application_types=[CaseTypeSubTypeEnum.STANDARD])
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_allowed_application_types_failure(self):
        application = self.create_standard_application_case(self.organisation)

        @allowed_application_types(application_types=[CaseTypeSubTypeEnum.OPEN])
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("This operation can only be used on applications of type:" in resp.content.decode("utf-8"))

    def test_application_in_state_editable_success(self):
        application = self.create_standard_application_case(self.organisation)

        @application_in_state(is_editable=True)
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_application_in_state_editable_failure(self):
        application = self.create_standard_application_case(self.organisation)
        application_status = CaseStatusEnum.read_only_statuses()[0]
        application.status = CaseStatus.objects.get(status=application_status)
        application.save()

        @application_in_state(is_editable=True)
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

        @application_in_state(is_major_editable=True)
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=None, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_application_in_state_major_editable_failure(self):
        application = self.create_standard_application_case(self.organisation)
        application.status = CaseStatus.objects.get(status=CaseStatusEnum.read_only_statuses()[0])
        application.save()

        @application_in_state(is_major_editable=True)
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

    def test_authorised_to_view_application_hmrc_organisation_success(self):
        application = self.create_hmrc_query(self.organisation)
        request = _FakeRequest(self.exporter_user, application.hmrc_organisation)

        @authorised_to_view_application(ExporterUser)
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

    def test_authorised_to_view_application_wrong_hmrc_organisation_failure(self):
        application = self.create_hmrc_query(self.organisation)
        request = _FakeRequest(self.exporter_user, self.organisation)

        @authorised_to_view_application(ExporterUser)
        def a_view(request, *args, **kwargs):
            return HttpResponse()

        resp = a_view(request=request, pk=application.pk)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            "You can only perform this operation on an application that has been opened within your organisation"
            in resp.content.decode("utf-8")
        )
