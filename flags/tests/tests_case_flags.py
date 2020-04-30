from django.urls import reverse
from rest_framework import status

from flags.enums import FlagLevels
from flags.tests.factories import FlagFactory
from test_helpers.clients import DataTestClient


class CaseFlagsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.url = reverse("flags:case_flags", kwargs={"case_pk": self.case.pk})
        self.flag_1 = FlagFactory(level=FlagLevels.CASE, team=self.team)
        self.flag_2 = FlagFactory(level=FlagLevels.CASE, team=self.team)
        self.flags = [self.flag_1, self.flag_2]
        self.case.flags.set(self.flags)

    def test_get_case_flags(self):
        response = self.client.get(self.url, **self.gov_headers)
        response_data = [flag["name"] for flag in response.json()["flags"]]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data, sorted([flag.name for flag in self.flags]))

    def test_get_case_flags_which_block_approval(self):
        self.flag_1.blocks_approval = True
        self.flag_1.save()

        response = self.client.get(self.url + "?blocks_approval=True", **self.gov_headers)
        response_data = response.json()["flags"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["name"], self.flag_1.name)
