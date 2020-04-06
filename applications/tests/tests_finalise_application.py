from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from applications.enums import LicenceDuration
from applications.libraries.licence import get_default_duration
from licences.models import Licence
from audit_trail.models import Audit
from cases.enums import AdviceType, CaseTypeEnum
from conf.constants import GovPermissions
from lite_content.lite_api import strings
from static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from users.models import Role


class FinaliseApplicationTests(DataTestClient):
    def _set_user_permission(self, permissions: list):
        self.gov_user.role = self.role
        self.gov_user.role.permissions.set([permission.name for permission in permissions])
        self.gov_user.save()

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.url = reverse("applications:finalise", kwargs={"pk": self.standard_application.id})
        self.role = Role.objects.create(name="test")
        self.finalised_status = CaseStatus.objects.get(status="finalised")
        self.date = timezone.now()
        self.post_date = {"year": self.date.year, "month": self.date.month, "day": self.date.day}

    def test_approve_application_success(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": AdviceType.APPROVE, "duration": 60}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()
        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["application"], str(self.standard_application.id))
        self.assertEqual(response_data["start_date"], self.date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["duration"], data["duration"])
        self.assertFalse(response_data["is_complete"])
        self.assertTrue(Licence.objects.filter(application=self.standard_application, is_complete=False).exists())

        # The case should not be finalised until the case is complete
        self.assertNotEqual(self.standard_application.status, self.finalised_status)

    def test_default_duration_no_permission_finalise_success(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE])
        data = {"action": AdviceType.APPROVE, "duration": get_default_duration(self.standard_application)}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["duration"], data["duration"])
        self.assertTrue(Licence.objects.filter(application=self.standard_application, is_complete=False).exists())

    def test_no_duration_finalise_success(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE])
        data = {"action": AdviceType.APPROVE}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["duration"], get_default_duration(self.standard_application))
        self.assertTrue(Licence.objects.filter(application=self.standard_application, is_complete=False).exists())

    def test_no_permissions_finalise_failure(self):
        self._set_user_permission([])
        data = {"action": AdviceType.APPROVE}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_finalise_clearance_application_success(self):
        clearance_application = self.create_mod_clearance_application(
            self.organisation, case_type=CaseTypeEnum.EXHIBITION
        )
        self._set_user_permission(
            [GovPermissions.MANAGE_CLEARANCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION]
        )
        data = {"action": AdviceType.APPROVE, "duration": 13}
        data.update(self.post_date)

        url = reverse("applications:finalise", kwargs={"pk": clearance_application.pk})
        response = self.client.put(url, data=data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response_data["application"], str(clearance_application.id))
        self.assertEqual(response_data["start_date"], self.date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["duration"], data["duration"])
        self.assertFalse(response_data["is_complete"])
        self.assertTrue(Licence.objects.filter(application=clearance_application, is_complete=False).exists())

    def test_set_duration_permission_denied(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE])
        data = {"action": AdviceType.APPROVE, "duration": 13}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json(), {"errors": [strings.Applications.Generic.Finalise.Error.SET_DURATION_PERMISSION]}
        )

    def test_invalid_duration_data(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": AdviceType.APPROVE, "duration": LicenceDuration.MAX.value + 1}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"errors": {"non_field_errors": [strings.Applications.Generic.Finalise.Error.DURATION_RANGE]}},
        )

    def test_no_start_date_failure(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": AdviceType.APPROVE, "duration": 20}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(), {"errors": {"start_date": [strings.Applications.Finalise.Error.MISSING_DATE]}}
        )

    def test_no_action_failure(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE])

        response = self.client.put(self.url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": [strings.Applications.Finalise.Error.NO_ACTION_GIVEN]})

    def test_refuse_application_success(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE])

        data = {"action": AdviceType.REFUSE}
        response = self.client.put(self.url, data=data, **self.gov_headers)
        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["application"], str(self.standard_application.id))
        self.assertEqual(self.standard_application.status, self.finalised_status)
        self.assertEqual(Audit.objects.count(), 1)
