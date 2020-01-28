from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class FlagsListTests(DataTestClient):
    url = reverse("flags:flags")

    def test_gov_user_can_see_all_flags(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_gov_user_can_see_only_filtered_case_level_and_team_flags(self):
        other_team = self.create_team("Team")

        flag1 = self.create_flag("Flag1", "Case", self.team)
        flag2 = self.create_flag("Flag2", "Organisation", self.team)
        flag3 = self.create_flag("Flag3", "Case", other_team)
        flag4 = self.create_flag("Flag4", "Case", self.team)

        response = self.client.get(self.url + "?level=Case&team=" + self.team.name, **self.gov_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_flags = [flag["id"] for flag in response_data["flags"]]
        self.assertIn(str(flag1.id), returned_flags)
        self.assertNotIn(str(flag2.id), returned_flags)
        self.assertNotIn(str(flag3.id), returned_flags)
        self.assertIn(str(flag4.id), returned_flags)
