from django.http import HttpResponse
from rest_framework import status

from cases.enums import CaseTypeSubTypeEnum
from conf.decorators import allowed_application_types, application_in_state
from lite_content.lite_api import strings
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient


# class DecoratorTests(DataTestClient):
#     def test_allowed_application_types_success(self):
#         application = self.create_standard_application_case(self.organisation)
#
#         @allowed_application_types(application_types=[CaseTypeSubTypeEnum.STANDARD])
#         def a_view(kwargs):
#             return HttpResponse()
#
#         resp = a_view(request=None, pk=application.pk)
#         self.assertEqual(resp.status_code, status.HTTP_200_OK)
#
#     def test_allowed_application_types_failure(self):
#         application = self.create_standard_application_case(self.organisation)
#
#         @allowed_application_types(application_types=[CaseTypeSubTypeEnum.OPEN])
#         def a_view(kwargs):
#             return HttpResponse()
#
#         resp = a_view(request=None, pk=application.pk)
#         self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertTrue("This operation can only be used on applications of type:" in resp.content.decode('utf-8'))
#
#     def test_application_in_state_editable_success(self):
#         application = self.create_standard_application_case(self.organisation)
#
#         @application_in_state(is_editable=True)
#         def a_view(kwargs):
#             return HttpResponse()
#
#         resp = a_view(request=None, pk=application.pk)
#         self.assertEqual(resp.status_code, status.HTTP_200_OK)
#
#     def test_application_in_state_editable_failure(self):
#         application = self.create_standard_application_case(self.organisation)
#         application_status = CaseStatusEnum.read_only_statuses()[0]
#         application.status = CaseStatus.objects.get(status=application_status)
#         application.save()
#
#         @application_in_state(is_editable=True)
#         def a_view(kwargs):
#             return HttpResponse()
#
#         resp = a_view(request=None, pk=application.pk)
#         self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertTrue(f"Application status {application_status} is read-only." in resp.content.decode('utf-8'))
#
#     def test_application_in_state_major_editable_success(self):
#         application = self.create_standard_application_case(self.organisation)
#         application.status = CaseStatus.objects.get(status=CaseStatusEnum.major_editable_statuses()[0])
#         application.save()
#
#         @application_in_state(is_major_editable=True)
#         def a_view(kwargs):
#             return HttpResponse()
#
#         resp = a_view(request=None, pk=application.pk)
#         self.assertEqual(resp.status_code, status.HTTP_200_OK)
#
#     def test_application_in_state_major_editable_failure(self):
#         application = self.create_standard_application_case(self.organisation)
#         application.status = CaseStatus.objects.get(status=CaseStatusEnum.read_only_statuses()[0])
#         application.save()
#
#         @application_in_state(is_major_editable=True)
#         def a_view(kwargs):
#             return HttpResponse()
#
#         resp = a_view(request=None, pk=application.pk)
#         self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertTrue(strings.Applications.Generic.NOT_POSSIBLE_ON_MINOR_EDIT in resp.content.decode('utf-8'))
#
#     #TODO test authorised_to_view_application
