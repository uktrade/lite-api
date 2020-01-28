from django.urls import reverse
from rest_framework import status

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

        response = self.client.get(self.url + "?level=Case&team=" + self.team.name, **self.gov_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_flags = [flag["id"] for flag in response_data["flags"]]
        self.assertIn(str(flag1.id), returned_flags)
        self.assertNotIn(str(org_level_flag.id), returned_flags)
        self.assertNotIn(str(other_team_flag.id), returned_flags)
        self.assertIn(str(flag4.id), returned_flags)
