from django.urls import reverse

from rest_framework import status
from rest_framework.serializers import ValidationError

from test_helpers.clients import DataTestClient

from api.flags.enums import FlagPermissions

from api.flags.tests.factories import FlagFactory


class CaseFlagsManagementTests(DataTestClient):
    def setUp(self):
        super().setUp()

        # Cases
        self.case = self.create_standard_application_case(organisation=self.organisation)
        self.case.flags.all().delete()

        # Teams
        self.other_team = self.create_team("Team")

        # Flags
        self.team_case_flag_1 = self.create_flag("Case Flag 1", "Case", self.team)
        self.team_case_flag_2 = self.create_flag("Case Flag 2", "Case", self.team)
        self.team_org_flag = self.create_flag("Org Flag 1", "Organisation", self.team)
        self.other_team_case_flag = self.create_flag("Other Team Case Flag", "Case", self.other_team)
        self.all_flags = [
            self.team_case_flag_1,
            self.team_org_flag,
            self.team_case_flag_2,
            self.other_team_case_flag,
        ]

        self.case_url = reverse("cases:case", kwargs={"pk": self.case.id})
        self.case_flag_url = reverse("flags:assign_flags")
        self.audit_url = reverse("cases:activity", kwargs={"pk": self.case.id})

    def test_no_flags_for_case_are_returned(self):
        """
        Given a Case with no Flags assigned
        When a user requests the Case
        Then the correct Case with an empty Flag list is returned
        """
        response = self.client.get(self.case_url, **self.gov_headers)

        self.assertEqual([], response.json()["case"]["flags"])

    def test_all_flags_for_case_are_returned(self):
        """
        Given a Case with Flags already assigned
        When a user requests the Case
        Then the correct Case with all assigned Flags are returned
        """
        self.case.flags.set(self.all_flags)

        response = self.client.get(self.case_url, **self.gov_headers)
        returned_case = response.json()["case"]

        self.assertEqual(len(self.case.flags.all()), len(returned_case["flags"]))

    def test_user_can_add_case_level_flags_from_their_own_team(self):
        """
        Given a Case with no Flags assigned
        When a user attempts to add a case-level Flag owned by their Team to the Case
        Then the Flag is successfully added
        """
        flags_to_add = {
            "level": "cases",
            "objects": [self.case.id],
            "flags": [self.team_case_flag_1.pk],
        }

        self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        self.assertEqual(len(flags_to_add["flags"]), len(self.case.flags.all()))
        self.assertTrue(self.team_case_flag_1 in self.case.flags.all())

    def test_user_can_add_case_level_flags_as_applicable_team(self):
        """
        Given a Case with no Flags assigned
        When a user attempts to add a case-level Flag which are applicable by their Team to the Case
        Then the Flag is successfully added
        """
        owner_team = self.create_team("OwnerTeam")

        applicable_flag_flag = self.create_flag("Flag1", "Case", owner_team)
        applicable_flag_flag.applicable_by_team.set([self.team])
        applicable_flag_flag.save()

        flags_to_add = {
            "level": "cases",
            "objects": [self.case.id],
            "flags": [applicable_flag_flag.pk],
        }

        self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        self.assertEqual(len(flags_to_add["flags"]), len(self.case.flags.all()))
        self.assertTrue(applicable_flag_flag in self.case.flags.all())

    def test_user_cannot_assign_flags_that_are_not_owned_by_their_team(self):
        """
        Given a Case with no Flags assigned
        When a user attempts to add a case-level Flag not owned by their Team to the Case
        Then the Flag is not added
        """
        flags_to_add = {
            "level": "cases",
            "objects": [self.case.id],
            "flags": [self.other_team_case_flag.pk],
        }
        other_team_2 = self.create_team("Team2")
        self.other_team_case_flag.applicable_by_team.set([other_team_2])
        self.other_team_case_flag.save()

        response = self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        self.assertEqual(0, len(self.case.flags.all()))
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_user_cannot_assign_flags_that_are_not_case_level(self):
        """
        Given a Case with no Flags assigned
        When a user attempts to add a non-case-level Flag owned by their Team to the Case
        Then the Flag is not added
        """
        flags_to_add = {
            "level": "cases",
            "objects": [self.case.id],
            "flags": [self.team_org_flag.pk],
        }

        response = self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        self.assertEqual(0, len(self.case.flags.all()))
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_when_one_flag_is_removed_then_other_flags_are_unaffected(self):
        """
        Given a Case with Flags already assigned
        When a user removes a case-level Flag owned by their Team from the Case
        Then only that Flag is removed
        """

        # Arrange (note that the endpoint expects flags being PUT to the case, therefore the flag being removed is not
        # included in the request body)
        self.case.flags.set(self.all_flags)
        flags_to_keep = {
            "level": "cases",
            "objects": [self.case.id],
            "flags": [self.team_case_flag_2.pk],
        }
        self.all_flags.remove(self.team_case_flag_1)

        self.client.put(self.case_flag_url, flags_to_keep, **self.gov_headers)

        self.assertEqual(len(self.all_flags), len(self.case.flags.all()))
        for flag in self.all_flags:
            self.assertTrue(flag in self.case.flags.all())

    def test_user_can_add_approval_blocking_flags(self):
        """
        Given a Case with no Flags assigned
        And a Flag that blocks application approval
        When a user attempts to add this Flag
        Then the Flag is successfully added
        """

        approval_blocking_flag = FlagFactory(
            name="Approval blocking flag", level="Case", team=self.team, blocks_finalising=True
        )

        flags_to_add = {
            "level": "cases",
            "objects": [self.case.id],
            "flags": [approval_blocking_flag.pk],
        }

        self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        self.assertEqual(len(flags_to_add["flags"]), len(self.case.flags.all()))
        self.assertTrue(approval_blocking_flag in self.case.flags.all())

    def test_user_can_add_approval_blocking_flags_with_special_permissions(self):
        """
        Given a Case with no Flags assigned
        And a Flag that blocks application approval
        And the Flag requires special permissions to remove it
        When a user attempts to add this Flag
        Then the Flag is successfully added
        """

        approval_blocking_flag = FlagFactory(
            name="Approval blocking flag",
            level="Case",
            team=self.team,
            blocks_finalising=True,
            removable_by=FlagPermissions.AUTHORISED_COUNTERSIGNER,
        )

        flags_to_add = {
            "level": "cases",
            "objects": [self.case.id],
            "flags": [approval_blocking_flag.pk],
        }

        self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        self.assertEqual(len(flags_to_add["flags"]), len(self.case.flags.all()))
        self.assertTrue(approval_blocking_flag in self.case.flags.all())

    def test_user_cannot_remove_approval_blocking_flags_that_have_special_permissions(self):
        """
        Given a Case with a Flag that blocks application approval
        And the Flag requires special permissions to remove it
        When a user without this permission attempts to remove this Flag
        Then an error is raised
        """

        approval_blocking_flag = FlagFactory(
            name="Approval blocking flag",
            level="Case",
            team=self.team,
            blocks_finalising=True,
            removable_by=FlagPermissions.AUTHORISED_COUNTERSIGNER,
        )

        self.case.flags.set([approval_blocking_flag])

        flags_to_add = {
            "level": "cases",
            "objects": [self.case.id],
            "flags": [],
        }

        self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        self.assertEqual(1, len(self.case.flags.all()))
        self.assertTrue(approval_blocking_flag in self.case.flags.all())
        self.assertRaises(ValidationError)
