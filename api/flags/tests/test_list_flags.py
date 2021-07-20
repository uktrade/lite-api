import pytest
from django.urls import reverse
from rest_framework import status

from api.flags.enums import SystemFlags, FlagLevels
from api.flags.tests.factories import FlagFactory
from test_helpers.clients import DataTestClient


class FlagsListTests(DataTestClient):
    url = reverse("flags:flags")

    def test_gov_user_can_see_all_flags(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_gov_user_can_see_only_filtered_case_level_and_team_flags(self):
        """
        Given Gov user
        When searching for flags
        And case-level and team-level flags are set in the query params
        Then only the case-level and team-level flags are returned
        """
        other_team = self.create_team("Team")

        flag1 = self.create_flag("Flag1", "Case", self.team)
        org_level_flag = self.create_flag("Flag2", "Organisation", self.team)
        other_team_flag = self.create_flag("Flag3", "Case", other_team)
        flag4 = self.create_flag("Flag4", "Case", self.team)

        url = f"{self.url}?level=Case&team={self.team.id}&include_deactivated=False"
        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_flags = [flag["id"] for flag in response_data["results"]]
        self.assertIn(str(flag1.id), returned_flags)
        self.assertNotIn(str(org_level_flag.id), returned_flags)
        self.assertNotIn(str(other_team_flag.id), returned_flags)
        self.assertIn(str(flag4.id), returned_flags)
        self.assertNotIn(SystemFlags.GOOD_NOT_YET_VERIFIED_ID, returned_flags)

    def test_get_case_flags_which_block_approval(self):
        case = self.create_standard_application_case(self.organisation)
        flag_1 = FlagFactory(level=FlagLevels.CASE, team=self.team, blocks_finalising=True)
        flag_2 = FlagFactory(level=FlagLevels.CASE, team=self.team)
        flags = [flag_1, flag_2]
        case.flags.set(flags)

        response = self.client.get(
            self.url + f"?case={case.pk}&only_show_deactivated=False&blocks_finalising=True&disable_pagination=True",
            **self.gov_headers,
        )
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["name"], flag_1.name)

    def test_include_system_flags_filter(self):
        """Test that the include_system_flags filter works properly."""

        def get_flags_count(system_flags):
            response = self.client.get(self.url + f"?include_system_flags={system_flags}", **self.gov_headers)
            return response.json()["count"]

        assert get_flags_count(True) > get_flags_count(False)
