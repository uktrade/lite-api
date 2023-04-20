import pytest

from datetime import datetime
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from rest_framework import status

from api.applications.enums import LicenceDuration
from api.applications.views.helpers.advice import CounterSignatureIncompleteError
from api.applications.libraries.licence import get_default_duration
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.cases.enums import AdviceType, CaseTypeEnum, AdviceLevel, CountersignOrder
from api.cases.models import Advice, Case
from api.cases.tests.factories import CountersignAdviceFactory
from api.core.constants import GovPermissions
from api.flags.enums import FlagLevels
from api.flags.models import Flag
from api.flags.tests.factories import FlagFactory
from api.licences.enums import LicenceStatus
from api.licences.models import Licence, GoodOnLicence
from lite_content.lite_api import strings
from api.staticdata.statuses.models import CaseStatus
from api.teams.enums import TeamIdEnum
from api.teams.models import Team
from test_helpers.clients import DataTestClient
from api.users.models import Role

from lite_routing.routing_rules_internal.enums import FlagsEnum


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
        self.assertEqual(response_data["case"], str(self.standard_application.id))
        self.assertEqual(response_data["reference_code"], f"{self.standard_application.reference_code}")
        self.assertEqual(response_data["start_date"], self.date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["duration"], data["duration"])
        self.assertEqual(response_data["status"], LicenceStatus.DRAFT)
        self.assertTrue(Licence.objects.filter(case=self.standard_application, status=LicenceStatus.DRAFT).exists())

        # The case should not be finalised until the case is complete
        self.assertNotEqual(self.standard_application.status, self.finalised_status)

    def test_approve_application_reissue_success(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE])
        existing_licence = self.create_licence(self.standard_application, status=LicenceStatus.ISSUED)
        data = {"action": AdviceType.APPROVE, "duration": existing_licence.duration}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()
        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["case"], str(self.standard_application.id))
        self.assertEqual(response_data["reference_code"], self.standard_application.reference_code + "/A")
        self.assertEqual(response_data["start_date"], self.date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["duration"], data["duration"])
        self.assertEqual(response_data["status"], LicenceStatus.DRAFT)
        # Check existing Licence & new draft Licence are present
        self.assertEqual(Licence.objects.filter(case=self.standard_application).count(), 2)
        self.assertTrue(Licence.objects.filter(case=self.standard_application, status=LicenceStatus.DRAFT).exists())
        self.assertTrue(Licence.objects.filter(case=self.standard_application, status=LicenceStatus.ISSUED).exists())

    def test_approve_application_override_draft_success(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        existing_licence = self.create_licence(self.standard_application, status=LicenceStatus.DRAFT)
        data = {"action": AdviceType.APPROVE, "duration": existing_licence.duration + 1}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()
        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["case"], str(self.standard_application.id))
        self.assertEqual(response_data["reference_code"], f"{self.standard_application.reference_code}")
        self.assertEqual(response_data["start_date"], self.date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["duration"], data["duration"])
        self.assertEqual(response_data["status"], LicenceStatus.DRAFT)
        # Check existing draft licence is replaced
        self.assertEqual(Licence.objects.filter(case=self.standard_application).count(), 1)
        self.assertEqual(Licence.objects.get(case=self.standard_application).duration, data["duration"])

    def test_default_duration_no_permission_finalise_success(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE])
        data = {"action": AdviceType.APPROVE, "duration": get_default_duration(self.standard_application)}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["duration"], data["duration"])
        self.assertTrue(Licence.objects.filter(case=self.standard_application, status=LicenceStatus.DRAFT).exists())

    def test_no_duration_finalise_success(self):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE])
        data = {"action": AdviceType.APPROVE}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["duration"], get_default_duration(self.standard_application))
        self.assertTrue(Licence.objects.filter(case=self.standard_application, status=LicenceStatus.DRAFT).exists())

    def test_no_permissions_finalise_failure(self):
        self._set_user_permission([])
        data = {"action": AdviceType.APPROVE}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_application_blocking_flags_failure(self):
        flag = FlagFactory(level=FlagLevels.CASE, team=self.team, blocks_finalising=True)
        self.standard_application.flags.add(flag)
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": AdviceType.APPROVE, "duration": 60}
        data.update(self.post_date)

        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_data["errors"], [f"{strings.Applications.Finalise.Error.BLOCKING_FLAGS}{flag.name}"])

    def test_finalise_clearance_application_success(self):
        clearance_application = self.create_mod_clearance_application_case(
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["case"], str(clearance_application.id))
        self.assertEqual(response_data["reference_code"], f"{clearance_application.reference_code}")
        self.assertEqual(response_data["start_date"], self.date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["duration"], data["duration"])
        self.assertEqual(response_data["status"], LicenceStatus.DRAFT)
        self.assertTrue(Licence.objects.filter(case=clearance_application, status=LicenceStatus.DRAFT).exists())

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
            response.json(), {"errors": {"start_date": [strings.Applications.Finalise.Error.INVALID_DATE]}}
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
        self.assertEqual(Audit.objects.count(), 1)

    def test_reissue_after_product_assessment_changes(self):
        """
        Test to check products on licence are correctly updated after product assessment changes

        1. Initially we finalise an application to create a draft licence.
        2. Now we update product assessment for few products on the application and try to finalise
        without consolidating the advice. In this case products on the licence are not going to be
        affected as we have not consolidated the advice.
        3. Finally we consolidate the advice and finalise the application again. This time the
        changes are picked up and only products that require licence are associated to the licence.
        """
        # Approve existing product on the application
        self.create_advice(
            self.gov_user,
            self.standard_application,
            "good",
            AdviceType.APPROVE,
            AdviceLevel.FINAL,
            advice_text="approve",
        )

        # Add few more products
        for i in range(3):
            good_on_app = self.create_good_on_application(
                self.standard_application, self.create_good(f"product{i+2}", self.organisation)
            )
            self.create_advice(
                self.gov_user,
                self.standard_application,
                "",
                AdviceType.APPROVE,
                AdviceLevel.FINAL,
                good=good_on_app.good,
            )

        # get the finalise form
        response = self.client.get(self.url, **self.gov_headers)
        data = response.json()["goods"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 4)

        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": AdviceType.APPROVE, "duration": 60}
        for good_on_app in self.standard_application.goods.all():
            data[f"quantity-{good_on_app.id}"] = str(good_on_app.quantity)
            data[f"value-{good_on_app.id}"] = str(good_on_app.value)

        data.update(self.post_date)

        # finalise the application
        # this creates draft licence - it becomes active when published to exporter
        # for the purpose of this test that is not required
        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()
        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["case"], str(self.standard_application.id))
        self.assertEqual(response_data["reference_code"], f"{self.standard_application.reference_code}")
        self.assertEqual(response_data["status"], LicenceStatus.DRAFT)
        self.assertTrue(Licence.objects.filter(case=self.standard_application, status=LicenceStatus.DRAFT).exists())

        # Update product assessment on two products to NLR
        for good_on_app in list(self.standard_application.goods.all())[-2:]:
            good_on_app.is_good_controlled = False

        # try to finalise again without consolidating
        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()
        self.standard_application.refresh_from_db()
        licence = Licence.objects.filter(case=self.standard_application, status=LicenceStatus.DRAFT).first()
        self.assertEqual(licence.goods.count(), 4)

        # consolidate advice now
        for good_on_app in list(self.standard_application.goods.all())[-2:]:
            advice = good_on_app.good.advice.filter(level=AdviceLevel.FINAL)
            self.assertEqual(advice.count(), 1)
            advice = advice.first()
            advice.type = AdviceType.NO_LICENCE_REQUIRED
            advice.save()

        # finalise again
        response = self.client.put(self.url, data=data, **self.gov_headers)
        response_data = response.json()
        self.standard_application.refresh_from_db()

        # Ensure only products that require licence are associated to the licence
        licence = Licence.objects.filter(case=self.standard_application, status=LicenceStatus.DRAFT).first()
        self.assertEqual(licence.goods.count(), 2)

    @parameterized.expand(
        [
            FlagsEnum.LU_COUNTER_REQUIRED,
            FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
            FlagsEnum.MANPADS,
            FlagsEnum.AP_LANDMINE,
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_finalise_application_failure_with_countersigning_flags_but_no_countersignatures(self, flag_id):
        flag = Flag.objects.get(id=flag_id)
        self.standard_application.flags.add(flag)
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": AdviceType.APPROVE, "duration": 60}
        data.update(self.post_date)

        self.gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        self.gov_user.save()

        with pytest.raises(CounterSignatureIncompleteError) as err:
            self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(
            str(err.value),
            "This applications requires countersigning and the required countersignatures are not completed",
        )

    def _setup_advice_for_application(self, application, advice_type, advice_level):
        # Create Advice objects for all entities
        for good_on_application in application.goods.all():
            self.create_advice(
                self.gov_user,
                application,
                "",
                advice_type,
                advice_level,
                good=good_on_application.good,
            )
        for party_on_application in application.parties.all():
            self.create_advice(
                self.gov_user,
                application,
                party_on_application.party.type,
                advice_type,
                advice_level,
            )

    @parameterized.expand(
        [
            [
                ({"order": CountersignOrder.FIRST_COUNTERSIGN, "reject": True},),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                ),
            ],
            [
                (
                    {"order": CountersignOrder.FIRST_COUNTERSIGN, "reject": False},
                    {"order": CountersignOrder.SECOND_COUNTERSIGN, "reject": True},
                ),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                    {"id": FlagsEnum.MANPADS, "level": FlagLevels.CASE},
                ),
            ],
            [
                (
                    {"order": CountersignOrder.FIRST_COUNTERSIGN, "reject": False},
                    {"order": CountersignOrder.SECOND_COUNTERSIGN, "skip": True},
                ),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                    {"id": FlagsEnum.MANPADS, "level": FlagLevels.CASE},
                ),
            ],
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_finalise_application_failure_with_insufficient_countersignatures(self, countersign_data, flags):
        """Test to ensure if a particular countersigning is not fully approved then we raise error"""
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": AdviceType.APPROVE, "duration": 24}
        data.update(self.post_date)

        self.gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        self.gov_user.save()

        # setup flags
        for flag in flags:
            if flag["level"] == FlagLevels.CASE:
                self.standard_application.flags.add(Flag.objects.get(id=flag["id"]))
            if flag["level"] == FlagLevels.DESTINATION:
                for party_on_application in self.standard_application.parties.all():
                    party_on_application.party.flags.add(Flag.objects.get(id=flag["id"]))

        # Create Advice objects for all entities
        self._setup_advice_for_application(self.standard_application, AdviceType.APPROVE, AdviceLevel.FINAL)

        # Create Advice objects for all entities
        case = Case.objects.get(id=self.standard_application.id)
        advice_qs = Advice.objects.filter(case=case, level=AdviceLevel.FINAL, type=AdviceType.APPROVE)
        for countersign in countersign_data:
            if countersign.get("skip"):
                continue
            for index, advice in enumerate(list(advice_qs)):
                outcome_accepted = True
                if countersign.get("reject"):
                    outcome_accepted = False if index % 2 else True  # reject alternate advice

                CountersignAdviceFactory(
                    order=countersign["order"],
                    outcome_accepted=outcome_accepted,
                    reasons="countersigning reasons",
                    case=case,
                    advice=advice,
                )

        with pytest.raises(CounterSignatureIncompleteError) as err:
            self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(
            str(err.value),
            "This applications requires countersigning and the required countersignatures are not completed",
        )

    @parameterized.expand(
        [
            [
                (CountersignOrder.FIRST_COUNTERSIGN,),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                ),
            ],
            [
                (CountersignOrder.FIRST_COUNTERSIGN, CountersignOrder.SECOND_COUNTERSIGN),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                    {"id": FlagsEnum.MANPADS, "level": FlagLevels.CASE},
                ),
            ],
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_finalise_application_success_with_refuse_advice(self, required_countersign, flags):
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": AdviceType.APPROVE, "duration": 24}
        data.update(self.post_date)

        self.gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        self.gov_user.save()

        # setup flags
        for flag in flags:
            if flag["level"] == FlagLevels.CASE:
                self.standard_application.flags.add(Flag.objects.get(id=flag["id"]))
            if flag["level"] == FlagLevels.DESTINATION:
                for party_on_application in self.standard_application.parties.all():
                    party_on_application.party.flags.add(Flag.objects.get(id=flag["id"]))

        # Create Advice objects for all entities
        self._setup_advice_for_application(self.standard_application, AdviceType.REFUSE, AdviceLevel.FINAL)

        # Create Advice objects for all entities
        case = Case.objects.get(id=self.standard_application.id)
        advice_qs = Advice.objects.filter(case=case, level=AdviceLevel.FINAL, type=AdviceType.REFUSE)
        for order in required_countersign:
            for index, advice in enumerate(list(advice_qs)):
                CountersignAdviceFactory(
                    order=order,
                    outcome_accepted=True,
                    reasons="countersigning reasons",
                    case=case,
                    advice=advice,
                )

        response = self.client.put(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @parameterized.expand(
        [
            [AdviceType.APPROVE, (), (), ""],
            [
                AdviceType.APPROVE,
                (CountersignOrder.FIRST_COUNTERSIGN,),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                ),
                "removed the flag 'LU Countersign Required'.",
            ],
            [
                AdviceType.PROVISO,
                (CountersignOrder.FIRST_COUNTERSIGN,),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                ),
                "removed the flag 'LU Countersign Required'.",
            ],
            [
                AdviceType.NO_LICENCE_REQUIRED,
                (CountersignOrder.FIRST_COUNTERSIGN,),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                ),
                "removed the flag 'LU Countersign Required'.",
            ],
            [
                AdviceType.APPROVE,
                (CountersignOrder.FIRST_COUNTERSIGN, CountersignOrder.SECOND_COUNTERSIGN),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                    {"id": FlagsEnum.MANPADS, "level": FlagLevels.CASE},
                ),
                "removed the flags 'LU Countersign Required' and 'LU senior countersign required'.",
            ],
            [
                AdviceType.PROVISO,
                (CountersignOrder.FIRST_COUNTERSIGN, CountersignOrder.SECOND_COUNTERSIGN),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                    {"id": FlagsEnum.MANPADS, "level": FlagLevels.CASE},
                ),
                "removed the flags 'LU Countersign Required' and 'LU senior countersign required'.",
            ],
            [
                AdviceType.NO_LICENCE_REQUIRED,
                (CountersignOrder.FIRST_COUNTERSIGN, CountersignOrder.SECOND_COUNTERSIGN),
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                    {"id": FlagsEnum.MANPADS, "level": FlagLevels.CASE},
                ),
                "removed the flags 'LU Countersign Required' and 'LU senior countersign required'.",
            ],
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_finalise_application_success_with_countersigning(
        self, advice_type, required_countersign, flags, expected_text
    ):
        """Test to ensure if a particular countersigning order is fully approved then we can finalise Case"""
        self._set_user_permission([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE, GovPermissions.MANAGE_LICENCE_DURATION])
        data = {"action": advice_type, "duration": 24}
        data.update(self.post_date)
        for good_on_application in self.standard_application.goods.all():
            data[f"quantity-{str(good_on_application.id)}"] = good_on_application.quantity
            data[f"value-{str(good_on_application.id)}"] = good_on_application.value

        self.gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        self.gov_user.save()

        # setup flags
        for flag in flags:
            if flag["level"] == FlagLevels.CASE:
                self.standard_application.flags.add(Flag.objects.get(id=flag["id"]))
            if flag["level"] == FlagLevels.DESTINATION:
                # We emit audit entry of removing flags only if countersigning flags are set
                # on the Party and skip otherwise. To cover the case where we skip it, don't
                # set flags on one party (in this case last item is selected)
                for party_on_application in list(self.standard_application.parties.all())[:-1]:
                    party_on_application.party.flags.add(Flag.objects.get(id=flag["id"]))

        # Create Advice objects for all entities
        self._setup_advice_for_application(self.standard_application, advice_type, AdviceLevel.FINAL)

        # Create Advice objects for all entities
        case = Case.objects.get(id=self.standard_application.id)
        advice_qs = Advice.objects.filter(case=case, level=AdviceLevel.FINAL, type=advice_type)
        for order in required_countersign:
            for advice in advice_qs:
                CountersignAdviceFactory(
                    order=order, outcome_accepted=True, reasons="Agree with original outcome", case=case, advice=advice
                )

        response = self.client.put(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()

        # In case of NLR there won't be any products on the licence to finalise
        # so below details will be missing from the response
        if advice_type != AdviceType.NO_LICENCE_REQUIRED:
            self.assertEqual(response["reference_code"], case.reference_code)
            self.assertEqual(response["start_date"], datetime.strftime(datetime.now(), "%Y-%m-%d"))
            self.assertEqual(response["duration"], 24)

        # Assert Countersign flags removed from the Case
        expected_flags_to_remove = [FlagsEnum.LU_COUNTER_REQUIRED]
        if CountersignOrder.SECOND_COUNTERSIGN in required_countersign:
            expected_flags_to_remove.append(FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED)
        for flag_id in expected_flags_to_remove:
            flag = Flag.objects.get(id=flag_id)
            self.assertNotIn(flag, case.parameter_set())

        # Finally check for expected audit events
        audit_qs = Audit.objects.filter(verb=AuditType.DESTINATION_REMOVE_FLAGS, target_object_id=case.id)
        flag_names = sorted(list(Flag.objects.filter(id__in=expected_flags_to_remove).values_list("name", flat=True)))

        for item in audit_qs:
            audit_text = AuditSerializer(item).data["text"]
            self.assertEqual(audit_text, expected_text)
            self.assertEqual(sorted(item.payload["removed_flags"]), flag_names)


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
            AdviceLevel.FINAL,
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
            AdviceLevel.FINAL,
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
            AdviceLevel.FINAL,
            good=third_good_on_app.good,
        )

        response = self.client.get(self.url, **self.gov_headers)
        data = response.json()["goods"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 2)
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
            self.gov_user, self.standard_application, "good", AdviceType.PROVISO, AdviceLevel.FINAL
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
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)

    def test_approve_success(self):
        good_value = 1

        self.assertEqual(GoodOnLicence.objects.count(), 0)
        self.assertEqual(Licence.objects.count(), 0)

        self.data[f"quantity-{self.good_on_application.id}"] = self.good_on_application.quantity
        self.data[f"value-{self.good_on_application.id}"] = good_value

        response = self.client.put(self.url, data=self.data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(GoodOnLicence.objects.count(), 1)
        self.assertEqual(Licence.objects.count(), 1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["case"], str(self.standard_application.id))
        self.assertTrue(Licence.objects.filter(case=self.standard_application, status=LicenceStatus.DRAFT).exists())

        # validate licence
        licence = Licence.objects.get(case_id=self.standard_application.id)
        good_licence = GoodOnLicence.objects.get(licence=licence)

        self.assertEqual(good_licence.quantity, self.good_on_application.quantity)
        self.assertEqual(good_licence.value, good_value)

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
