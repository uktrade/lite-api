from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.enums import AdviceType
from cases.models import Case, Advice, TeamAdvice
from conf.constants import Permissions
from conf.helpers import convert_queryset_to_str
from teams.models import Team
from test_helpers.clients import DataTestClient
from users.models import GovUser, Role


class CreateCaseTeamAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.standard_application = self.create_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.standard_case = Case.objects.get(application=self.standard_application)

        self.role = Role(name="team_level")
        self.role.permissions.set(
            [Permissions.MANAGE_TEAM_ADVICE, Permissions.CONFIRM_OWN_ADVICE]
        )
        self.role.save()

        self.gov_user.role = self.role
        self.gov_user.save()

        self.gov_user_2 = GovUser(
            email="user@email.com", team=self.team, role=self.role
        )
        self.gov_user_3 = GovUser(
            email="users@email.com", team=self.team, role=self.role
        )
        self.gov_user_2.save()
        self.gov_user_3.save()

        self.open_application = self.create_open_application(self.organisation)
        self.submit_application(self.open_application)
        self.open_case = Case.objects.get(application=self.open_application)

        self.standard_case_url = reverse(
            "cases:case_team_advice", kwargs={"pk": self.standard_case.id}
        )
        self.open_case_url = reverse(
            "cases:case_team_advice", kwargs={"pk": self.open_case.id}
        )

    def test_advice_is_concatenated_when_team_advice_first_created(self):
        """
        Team advice is created on first call
        """
        self.create_advice(
            self.gov_user, self.standard_case, "end_user", AdviceType.PROVISO, Advice
        )
        self.create_advice(
            self.gov_user_2, self.standard_case, "end_user", AdviceType.PROVISO, Advice
        )
        self.create_advice(
            self.gov_user,
            self.standard_case,
            "good",
            AdviceType.NO_LICENCE_REQUIRED,
            Advice,
        )
        self.create_advice(
            self.gov_user_2,
            self.standard_case,
            "good",
            AdviceType.NO_LICENCE_REQUIRED,
            Advice,
        )

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0].get("type").get("key"), "proviso")
        self.assertEqual(response_data[1].get("type").get("key"), "no_licence_required")

    def test_create_conflicting_team_advice_shows_all_fields(self):
        """
        The type should show conflicting if there are conflicting types in the advice on a single object
        """
        self.create_advice(
            self.gov_user,
            self.standard_case,
            "good",
            AdviceType.NO_LICENCE_REQUIRED,
            Advice,
        )
        self.create_advice(
            self.gov_user_2, self.standard_case, "good", AdviceType.REFUSE, Advice
        )
        self.create_advice(
            self.gov_user_3, self.standard_case, "good", AdviceType.PROVISO, Advice
        )

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"][0]

        self.assertEqual(response_data.get("type").get("key"), "conflicting")
        self.assertEqual(response_data.get("proviso"), "I am easy to proviso")
        self.assertCountEqual(["1a", "1b", "1c"], response_data["denial_reasons"])

    # Normal restrictions on team advice items
    @parameterized.expand(
        [
            [AdviceType.APPROVE],
            [AdviceType.PROVISO],
            [AdviceType.REFUSE],
            [AdviceType.NO_LICENCE_REQUIRED],
            [AdviceType.NOT_APPLICABLE],
        ]
    )
    def test_create_end_user_case_team_advice(self, advice_type):
        """
        Tests that a gov user can create an approval/proviso/refuse/nlr/not_applicable
        piece of team level advice for an end user
        """
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": advice_type,
            "end_user": str(self.standard_application.end_user.id),
        }

        if advice_type == AdviceType.PROVISO:
            data["proviso"] = "I am easy to proviso"

        if advice_type == AdviceType.REFUSE:
            data["denial_reasons"] = ["1a", "1b", "1c"]

        response = self.client.post(
            self.standard_case_url, **self.gov_headers, data=[data]
        )
        response_data = response.json()["advice"][0]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response_data["text"], data["text"])
        self.assertEqual(response_data["note"], data["note"])
        self.assertEqual(response_data["type"]["key"], data["type"])
        self.assertEqual(response_data["end_user"], data["end_user"])

        advice_object = TeamAdvice.objects.get()

        # Ensure that proviso details aren't added unless the type sent is PROVISO
        if advice_type != AdviceType.PROVISO:
            self.assertTrue("proviso" not in response_data)
            self.assertEqual(advice_object.proviso, None)
        else:
            self.assertEqual(response_data["proviso"], data["proviso"])
            self.assertEqual(advice_object.proviso, data["proviso"])

        # Ensure that refusal details aren't added unless the type sent is REFUSE
        if advice_type != AdviceType.REFUSE:
            self.assertTrue("denial_reasons" not in response_data)
            self.assertEqual(advice_object.denial_reasons.count(), 0)
        else:
            self.assertCountEqual(
                response_data["denial_reasons"], data["denial_reasons"]
            )
            self.assertCountEqual(
                convert_queryset_to_str(
                    advice_object.denial_reasons.values_list("id", flat=True)
                ),
                data["denial_reasons"],
            )

    # User must have permission to create team advice
    def test_user_cannot_create_team_level_advice_without_permissions(self):
        """
        Tests that the right level of permissions are required
        """
        self.gov_user.role.permissions.set([])
        self.gov_user.save()
        response = self.client.get(self.standard_case_url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.standard_case_url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete(self.standard_case_url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_see_already_created_team_advice_without_additional_permissions(
        self,
    ):
        """
        No permissions are required to view any tier of advice
        """
        self.create_advice(
            self.gov_user, self.standard_case, "good", AdviceType.PROVISO, TeamAdvice
        )
        self.gov_user.role.permissions.set([])
        self.gov_user.save()
        response = self.client.get(self.standard_case_url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_can_view_other_teams_advice(self):
        """
        Advice is visible to all users, no matter which team it belongs to
        """
        self.create_advice(
            self.gov_user, self.standard_case, "good", AdviceType.PROVISO, TeamAdvice
        )
        self.create_advice(
            self.gov_user, self.standard_case, "end_user", AdviceType.REFUSE, TeamAdvice
        )

        team_2 = Team(name="2")
        team_2.save()
        self.gov_user.team = team_2
        self.gov_user.save()

        # Looks at the advice from the created which created it, using a user from another team
        url = reverse(
            "cases:view_team_advice",
            kwargs={"pk": self.standard_case.id, "team_pk": self.team.id},
        )

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json()["advice"]), 2)

    def test_advice_from_another_team_not_collated(self):
        """
        When collating advice, only the user's team's advice should be collated
        """
        self.create_advice(
            self.gov_user, self.standard_case, "good", AdviceType.PROVISO, Advice
        )
        team_2 = Team(name="2")
        team_2.save()
        self.gov_user_2.team = team_2
        self.gov_user_2.save()
        self.create_advice(
            self.gov_user_2, self.standard_case, "good", AdviceType.REFUSE, Advice
        )

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"]

        # Team 2's advice would conflict with team 1's if both were brought in
        self.assertNotEqual(response_data[0].get("type").get("key"), "conflicting")
        self.assertEqual(response_data[0].get("type").get("key"), "proviso")

    def test_cannot_submit_user_level_advice_if_team_advice_exists_for_that_team_on_that_case(
        self,
    ):
        """
        Logically blocks the submission of lower tier advice if higher tier advice exists
        """
        self.create_advice(
            self.gov_user_2, self.standard_case, "good", AdviceType.PROVISO, TeamAdvice
        )

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.standard_application.end_user.id),
        }

        response = self.client.post(
            reverse("cases:case_advice", kwargs={"pk": self.standard_case.id}),
            **self.gov_headers,
            data=[data]
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_submit_user_level_advice_if_team_advice_has_been_cleared_for_that_team_on_that_case(
        self,
    ):
        """
        No residual data is left to block lower tier advice being submitted after a clear
        """
        self.create_advice(
            self.gov_user_2, self.standard_case, "good", AdviceType.PROVISO, TeamAdvice
        )

        self.client.delete(self.standard_case_url, **self.gov_headers)

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.standard_application.end_user.id),
        }

        response = self.client.post(
            reverse("cases:case_advice", kwargs={"pk": self.standard_case.id}),
            **self.gov_headers,
            data=[data]
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_and_delete_audit_trail_is_created_when_the_appropriate_actions_take_place(
        self,
    ):
        """
        Audit trail is created when clearing or combining advice
        """
        self.create_advice(
            self.gov_user,
            self.standard_case,
            "end_user",
            AdviceType.NO_LICENCE_REQUIRED,
            Advice,
        )
        self.create_advice(
            self.gov_user_2, self.standard_case, "good", AdviceType.REFUSE, Advice
        )
        self.create_advice(
            self.gov_user_3, self.standard_case, "good", AdviceType.PROVISO, Advice
        )

        self.client.get(self.standard_case_url, **self.gov_headers)
        self.client.delete(self.standard_case_url, **self.gov_headers)

        response = self.client.get(
            reverse("cases:activity", kwargs={"pk": self.standard_case.id}),
            **self.gov_headers
        )

        self.assertEqual(len(response.json()["activity"]), 2)

    def test_creating_team_advice_does_not_overwrite_user_level_advice(self):
        """
        Because of the shared parent class, make sure the parent class "save" method is overridden by the child class
        """
        self.create_advice(
            self.gov_user,
            self.standard_case,
            "end_user",
            AdviceType.NO_LICENCE_REQUIRED,
            Advice,
        )
        self.create_advice(
            self.gov_user,
            self.standard_case,
            "end_user",
            AdviceType.NO_LICENCE_REQUIRED,
            TeamAdvice,
        )

        self.client.get(self.standard_case_url, **self.gov_headers)

        self.assertEqual(Advice.objects.count(), 2)

    @parameterized.expand(
        [
            [AdviceType.APPROVE],
            [AdviceType.PROVISO],
            [AdviceType.REFUSE],
            [AdviceType.NO_LICENCE_REQUIRED],
            [AdviceType.NOT_APPLICABLE],
        ]
    )
    def test_coalesce_merges_duplicate_advice_instead_of_appending_it_simple(
        self, advice_type
    ):
        """
        Makes sure we strip out duplicates of advice on the same object
        """
        self.create_advice(
            self.gov_user_2, self.standard_case, "good", advice_type, Advice
        )
        self.create_advice(
            self.gov_user_3, self.standard_case, "good", advice_type, Advice
        )

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"]

        self.assertNotIn("\n-------\n", response_data[0]["text"])

    def test_create_team_advice_without_confirm_own_advice_permission_when_user_advice_exists_failure(
        self,
    ):
        self.role.permissions.set([Permissions.MANAGE_TEAM_ADVICE])

        self.create_advice(
            self.gov_user, self.standard_case, "good", AdviceType.PROVISO, Advice
        )

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.standard_application.end_user.id),
        }

        response = self.client.post(
            reverse("cases:case_team_advice", kwargs={"pk": self.standard_case.id}),
            **self.gov_headers,
            data=[data]
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
