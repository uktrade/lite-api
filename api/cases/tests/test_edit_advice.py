import pytest

from copy import deepcopy
from django.test import override_settings
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.applications.models import StandardApplication
from api.applications.views.helpers.advice import CountersignInvalidAdviceTypeError
from api.cases.enums import AdviceType, AdviceLevel, CountersignOrder
from api.cases.models import Advice, CountersignAdvice
from api.cases.tests.factories import CountersignAdviceFactory
from api.core.constants import GovPermissions
from api.flags.enums import FlagLevels
from api.flags.models import Flag
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.teams.models import Team
from api.users.models import Role

from lite_routing.routing_rules_internal.enums import FlagsEnum
from test_helpers.clients import DataTestClient


class EditCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.case)
        self.application = StandardApplication.objects.get(id=self.case.id)
        self.url = reverse("cases:user_advice", kwargs={"pk": self.case.id})

    def test_edit_standard_case_advice_twice_only_shows_once(self):
        """
        Tests that a gov user cannot create two pieces of advice on the same
        case item (be that a good or destination)
        """
        data = {
            "type": AdviceType.APPROVE,
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "country": "GB",
            "level": AdviceLevel.USER,
        }

        self.client.post(self.url, **self.gov_headers, data=[data])
        self.client.post(self.url, **self.gov_headers, data=[data])

        # Assert that there's only one piece of advice
        self.assertEqual(Advice.objects.count(), 1)


class AdviceFinalLevelUpdateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.case)
        self.application = StandardApplication.objects.get(id=self.case.id)
        self.url = reverse("cases:case_final_advice", kwargs={"pk": self.case.id})
        permissions = [
            GovPermissions.MANAGE_LICENCE_FINAL_ADVICE,
            GovPermissions.MANAGE_LICENCE_DURATION,
        ]
        self.gov_user.role = Role.objects.create(name="Final Advice test")
        self.gov_user.role.permissions.set([permission.name for permission in permissions])
        self.gov_user.save()

        self._setup_advice_for_application(self.application, AdviceType.APPROVE, AdviceLevel.FINAL)
        self.advice_qs = Advice.objects.filter(case=self.case, level=AdviceLevel.FINAL, type=AdviceType.APPROVE)

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

    @parameterized.expand(CaseStatusEnum._terminal_statuses)
    def test_advice_cannot_be_edited_for_terminal_cases(self, case_status):
        self.case.status = CaseStatus.objects.get(status=case_status)
        self.case.save()

        data = [
            {
                "id": advice.id,
                "text": "updating previous recommendation with more details",
                "note": "No additional instructions",
            }
            for advice in self.advice_qs
        ]
        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            ["You can only perform this operation on a case in a non-terminal state"],
        )

    @parameterized.expand(
        [
            AdviceLevel.USER,
            AdviceLevel.TEAM,
        ]
    )
    def test_edit_advice_level_returns_error(self, level):
        data = [
            {
                "id": advice.id,
                "text": "updating previous recommendation with more details",
                "note": "No additional instructions",
                "level": level,
            }
            for advice in self.advice_qs
        ]
        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            ["Advice level cannot be updated once it is created"],
        )

    @parameterized.expand(
        [
            AdviceLevel.USER,
            AdviceLevel.TEAM,
        ]
    )
    def test_edit_advice_invalid_data_returns_error(self, level):
        data = [
            {
                "id": advice.id,
                "type": "invalid",
                "text": "updating previous recommendation with more details",
                "note": "No additional instructions",
            }
            for advice in self.advice_qs
        ]
        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            [
                {"type": ['"invalid" is not a valid choice.']},
                {"type": ['"invalid" is not a valid choice.']},
                {"type": ['"invalid" is not a valid choice.']},
                {"type": ['"invalid" is not a valid choice.']},
            ],
        )

    @parameterized.expand(
        [
            (
                AdviceType.APPROVE,
                {
                    "text": "updating previous recommendation with more details",
                    "proviso": "",
                    "note": "no additional instructions",
                    "denial_reasons": [],
                },
            ),
            (
                AdviceType.PROVISO,
                {
                    "text": "updating previous recommendation with more details",
                    "proviso": "Updated licence conditions",
                    "note": "with further instructions",
                    "denial_reasons": [],
                },
            ),
            (
                AdviceType.REFUSE,
                {
                    "text": "Recommending refuse",
                    "proviso": "",
                    "note": "",
                    "denial_reasons": ["1", "1d", "2", "4"],
                },
            ),
            (
                AdviceType.NO_LICENCE_REQUIRED,
                {
                    "text": "",
                    "proviso": "",
                    "note": "",
                    "denial_reasons": [],
                },
            ),
        ]
    )
    def test_edit_final_level_advice_types_success(self, advice_type, advice_data):
        Advice.objects.all().delete()

        self._setup_advice_for_application(self.application, advice_type, AdviceLevel.FINAL)
        advice_qs = Advice.objects.filter(case=self.case, level=AdviceLevel.FINAL, type=advice_type)
        advice_ids = advice_qs.values_list("id", flat=True)

        data = []
        for advice in advice_qs:
            entity_data = deepcopy(advice_data)
            entity_data["id"] = advice.id
            data.append(entity_data)

        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["advice"]
        for index, advice in enumerate(list(advice_qs)):
            advice.refresh_from_db()

            self.assertEqual(response[index]["text"], data[index]["text"])
            self.assertEqual(response[index]["proviso"], data[index]["proviso"])
            self.assertEqual(response[index]["note"], data[index]["note"])
            self.assertEqual(response[index]["denial_reasons"], data[index]["denial_reasons"])

            self.assertEqual(advice.text, data[index]["text"])
            self.assertEqual(advice.proviso, data[index]["proviso"])
            self.assertEqual(advice.note, data[index]["note"])
            self.assertEqual([d.id for d in advice.denial_reasons.all()], data[index]["denial_reasons"])

        ids_after_update = Advice.objects.filter(case=self.case, level=AdviceLevel.FINAL, type=advice_type).values_list(
            "id", flat=True
        )
        self.assertEqual(sorted(advice_ids), sorted(ids_after_update))


class AdviceUpdateCountersignInvalidateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.case)
        self.application = StandardApplication.objects.get(id=self.case.id)
        self.url = reverse("cases:case_final_advice", kwargs={"pk": self.case.id})
        permissions = [
            GovPermissions.MANAGE_LICENCE_FINAL_ADVICE,
            GovPermissions.MANAGE_LICENCE_DURATION,
        ]
        self.gov_user.role = Role.objects.create(name="Final Advice test")
        self.gov_user.role.permissions.set([permission.name for permission in permissions])
        self.gov_user.save()

        self._setup_advice_for_application(self.application, AdviceType.APPROVE, AdviceLevel.FINAL)
        self.advice_qs = Advice.objects.filter(case=self.case, level=AdviceLevel.FINAL, type=AdviceType.APPROVE)

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
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                ),
                ((CountersignOrder.FIRST_COUNTERSIGN, False),),
                False,
            ],
            [
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                    {"id": FlagsEnum.MANPADS, "level": FlagLevels.CASE},
                ),
                (
                    (CountersignOrder.FIRST_COUNTERSIGN, True),
                    (CountersignOrder.SECOND_COUNTERSIGN, False),
                ),
                False,
            ],
            [
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                    {"id": FlagsEnum.MANPADS, "level": FlagLevels.CASE},
                ),
                (
                    (CountersignOrder.FIRST_COUNTERSIGN, True),
                    (CountersignOrder.SECOND_COUNTERSIGN, True),
                ),
                True,
            ],
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_countersignatures_invalidated_after_outcome_is_edited(
        self, flags, countersignatures, expected_countersign_status
    ):
        """
        Test to ensure Countersignatures are invalidated correctly after Caseworker edits their recommendation

        - initially creates Advice and CountersignAdvice for the expected order as per flags
        - Makes API call to edit caseworker's recommendation
        - Verifies that countersignatures are invalidated and their count matches.
        - `expected_countersign_status` is the expected CountersignAdvice status after editing recommendation

        Scenarios:
        1. Only licensing manager countersigning required and they reject the case
        2. Senior licensing manager countersigning required and they reject the case. In this case
           even if licensing manager accepts, that needs invalidating as the Case starts the journey
           from the beginning when it comes back again
        3. Both manager accepts - nothings needs invalidating in this case
        """
        # setup flags
        for flag in flags:
            if flag["level"] == FlagLevels.CASE:
                self.application.flags.add(Flag.objects.get(id=flag["id"]))
            if flag["level"] == FlagLevels.DESTINATION:
                # We emit audit entry of removing flags only if countersigning flags are set
                # on the Party and skip otherwise. To cover the case where we skip it, don't
                # set flags on one party (in this case last item is selected)
                for party_on_application in list(self.application.parties.all())[:-1]:
                    party_on_application.party.flags.add(Flag.objects.get(id=flag["id"]))

        self.gov_user.team = Team.objects.get(id="58e77e47-42c8-499f-a58d-94f94541f8c6")
        self.gov_user.save()

        countersign_orders = []

        for order, outcome in countersignatures:
            countersign_orders.append(order)
            for advice in self.advice_qs:
                CountersignAdviceFactory(
                    order=order,
                    valid=True,
                    outcome_accepted=outcome,
                    reasons="reasons",
                    case=self.case,
                    advice=advice,
                )
        self.assertEqual(
            CountersignAdvice.objects.filter(
                order__in=countersign_orders,
                case=self.case,
                valid=True,
            ).count(),
            self.advice_qs.count() * len(countersign_orders),
        )

        data = [
            {
                "id": advice.id,
                "text": "",
                "proviso": "",
                "note": "",
                "denial_reasons": [],
            }
            for advice in self.advice_qs
        ]
        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            CountersignAdvice.objects.filter(
                order__in=countersign_orders,
                case=self.case,
                valid=expected_countersign_status,
            ).count(),
            self.advice_qs.count() * len(countersign_orders),
        )

    @parameterized.expand(
        [
            [
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                ),
                ((CountersignOrder.FIRST_COUNTERSIGN, False),),
            ],
            [
                (
                    {"id": FlagsEnum.LU_COUNTER_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED, "level": FlagLevels.DESTINATION},
                    {"id": FlagsEnum.AP_LANDMINE, "level": FlagLevels.CASE},
                    {"id": FlagsEnum.MANPADS, "level": FlagLevels.CASE},
                ),
                (
                    (CountersignOrder.FIRST_COUNTERSIGN, True),
                    (CountersignOrder.SECOND_COUNTERSIGN, False),
                ),
            ],
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_countersignatures_invalidated_raises_error_for_refuse_outcome(self, flags, countersignatures):
        """
        Test to ensure Countersignatures are not invalidated when the original outcome is of REFUSE type
        """
        for advice in self.advice_qs:
            advice.type = AdviceType.REFUSE
            advice.text = "Recommending refuse"
            # advice.denial_reasons = ["1", "1b"]
            advice.save()

        # setup flags
        for flag in flags:
            if flag["level"] == FlagLevels.CASE:
                self.application.flags.add(Flag.objects.get(id=flag["id"]))
            if flag["level"] == FlagLevels.DESTINATION:
                # We emit audit entry of removing flags only if countersigning flags are set
                # on the Party and skip otherwise. To cover the case where we skip it, don't
                # set flags on one party (in this case last item is selected)
                for party_on_application in list(self.application.parties.all())[:-1]:
                    party_on_application.party.flags.add(Flag.objects.get(id=flag["id"]))

        self.gov_user.team = Team.objects.get(id="58e77e47-42c8-499f-a58d-94f94541f8c6")
        self.gov_user.save()

        countersign_orders = []

        for order, outcome in countersignatures:
            countersign_orders.append(order)
            for advice in self.advice_qs:
                CountersignAdviceFactory(
                    order=order,
                    valid=True,
                    outcome_accepted=outcome,
                    reasons="reasons",
                    case=self.case,
                    advice=advice,
                )
        self.assertEqual(
            CountersignAdvice.objects.filter(
                order__in=countersign_orders,
                case=self.case,
                valid=True,
            ).count(),
            self.advice_qs.count() * len(countersign_orders),
        )

        data = [
            {
                "id": advice.id,
                "text": "",
                "proviso": "",
                "note": "",
                "denial_reasons": [],
            }
            for advice in self.advice_qs
        ]

        with pytest.raises(CountersignInvalidAdviceTypeError) as err:
            self.client.put(self.url, **self.gov_headers, data=data)

        self.assertEqual(
            str(err.value),
            "Cannot invalidate countersignatures as the outcome is refused",
        )
