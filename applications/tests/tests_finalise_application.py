from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from applications.enums import LicenceDuration
from applications.libraries.licence import get_default_duration
from audit_trail.enums import AuditType
from audit_trail.models import Audit
from cases.enums import AdviceType, CaseTypeEnum, AdviceLevel
from conf.constants import GovPermissions
from flags.enums import FlagLevels
from flags.tests.factories import FlagFactory
from licences.models import Licence
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

    def test_approve_application_blocking_flags_failure(self):
        flag = FlagFactory(level=FlagLevels.CASE, team=self.team, blocks_approval=True)
        self.standard_application.flags.add(flag)
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": AdviceType.APPROVE, "duration": 60}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_data["errors"], [f"{strings.Applications.Finalise.Error.BLOCKING_FLAGS}{flag.name}"])

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
        self.assertEqual(Audit.objects.count(), 2)


class FinaliseApplicationGetApprovedGoodsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.url = reverse("applications:finalise", kwargs={"pk": self.standard_application.id})

    def test_get_approved_goods_success(self):
        # Approve the existing good
        advice_text = "looks good to me"
        self.create_advice(
            self.gov_user,
            self.standard_application,
            "good",
            AdviceType.APPROVE,
            AdviceLevel.USER,
            advice_text=advice_text,
        )

        # Refuse a second good
        second_good_on_app = self.create_good_on_application(
            self.standard_application, self.create_good("a thing", self.organisation)
        )
        self.create_advice(
            self.gov_user,
            self.standard_application,
            "",
            AdviceType.REFUSE,
            AdviceLevel.USER,
            good=second_good_on_app.good,
        )

        # NLR a third good
        third_good_on_app = self.create_good_on_application(
            self.standard_application, self.create_good("a thing", self.organisation)
        )
        self.create_advice(
            self.gov_user,
            self.standard_application,
            "",
            AdviceType.NO_LICENCE_REQUIRED,
            AdviceLevel.USER,
            good=third_good_on_app.good,
        )

        response = self.client.get(self.url, **self.gov_headers)
        data = response.json()["goods"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], str(self.good_on_application.id))
        self.assertEqual(data[0]["good"]["id"], str(self.good_on_application.good.id))
        self.assertEqual(data[0]["good"]["description"], self.good_on_application.good.description)
        self.assertEqual(data[0]["quantity"], self.good_on_application.quantity)
        self.assertEqual(data[0]["value"].split(".")[0], str(self.good_on_application.value))
        self.assertEqual(data[0]["advice"]["type"]["key"], AdviceType.APPROVE)
        self.assertEqual(data[0]["advice"]["text"], advice_text)

    def test_get_proviso_goods_success(self):
        # Proviso the existing good
        advice = self.create_advice(
            self.gov_user, self.standard_application, "good", AdviceType.PROVISO, AdviceLevel.USER
        )

        response = self.client.get(self.url, **self.gov_headers)
        data = response.json()["goods"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], str(self.good_on_application.id))
        self.assertEqual(data[0]["advice"]["text"], advice.text)
        self.assertEqual(data[0]["advice"]["proviso"], advice.proviso)


class FinaliseApplicationWithApprovedGoodsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.url = reverse("applications:finalise", kwargs={"pk": self.standard_application.id})
        self.date = timezone.now()
        self.data = {
            "action": AdviceType.APPROVE,
            "duration": get_default_duration(self.standard_application),
            "year": self.date.year,
            "month": self.date.month,
            "day": self.date.day,
        }
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.USER)

    def test_approve_success(self):
        self.data[f"quantity-{self.good_on_application.id}"] = self.good_on_application.quantity
        self.data[f"value-{self.good_on_application.id}"] = 1

        response = self.client.put(self.url, data=self.data, **self.gov_headers)
        response_data = response.json()
        self.good_on_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["application"], str(self.standard_application.id))
        self.assertTrue(Licence.objects.filter(application=self.standard_application, is_complete=False).exists())
        self.assertEqual(self.good_on_application.licenced_quantity, self.good_on_application.quantity)
        self.assertEqual(self.good_on_application.licenced_value, 1)

    def test_approve_no_value_failure(self):
        self.data[f"quantity-{self.good_on_application.id}"] = self.good_on_application.quantity

        response = self.client.put(self.url, data=self.data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data, {"errors": {f"value-{self.good_on_application.id}": [strings.Licence.NULL_VALUE_ERROR]}}
        )

    def test_approve_no_quantity_failure(self):
        self.data[f"value-{self.good_on_application.id}"] = 1

        response = self.client.put(self.url, data=self.data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data,
            {"errors": {f"quantity-{self.good_on_application.id}": [strings.Licence.NULL_QUANTITY_ERROR]}},
        )

    def test_approve_no_data_failure(self):
        response = self.client.put(self.url, data=self.data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data,
            {
                "errors": {
                    f"quantity-{self.good_on_application.id}": [strings.Licence.NULL_QUANTITY_ERROR],
                    f"value-{self.good_on_application.id}": [strings.Licence.NULL_VALUE_ERROR],
                }
            },
        )

    def test_approve_negative_quantity_failure(self):
        self.data[f"quantity-{self.good_on_application.id}"] = -1
        self.data[f"value-{self.good_on_application.id}"] = 1

        response = self.client.put(self.url, data=self.data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data,
            {"errors": {f"quantity-{self.good_on_application.id}": [strings.Licence.NEGATIVE_QUANTITY_ERROR]}},
        )

    def test_approve_negative_value_failure(self):
        self.data[f"quantity-{self.good_on_application.id}"] = 1
        self.data[f"value-{self.good_on_application.id}"] = -1

        response = self.client.put(self.url, data=self.data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data, {"errors": {f"value-{self.good_on_application.id}": [strings.Licence.NEGATIVE_VALUE_ERROR]}}
        )

    def test_approve_quantity_greater_than_applied_for_failure(self):
        self.data[f"quantity-{self.good_on_application.id}"] = self.good_on_application.quantity + 1
        self.data[f"value-{self.good_on_application.id}"] = 1

        response = self.client.put(self.url, data=self.data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data,
            {"errors": {f"quantity-{self.good_on_application.id}": [strings.Licence.INVALID_QUANTITY_ERROR]}},
        )
