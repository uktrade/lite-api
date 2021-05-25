from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.flags.enums import FlagLevels, FlagColours
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient


class FlagsCreateTest(DataTestClient):

    url = reverse("flags:flags")

    def test_gov_user_can_create_flags(self):
        data = {
            "name": "new flag",
            "level": "Organisation",
            "colour": FlagColours.ORANGE,
            "label": "This is label",
            "blocks_finalising": False,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["name"], "new flag")
        self.assertEqual(response_data["level"], "Organisation")
        self.assertEqual(response_data["colour"], FlagColours.ORANGE)
        self.assertEqual(response_data["label"], "This is label")
        self.assertEqual(
            response_data["team"], {"id": str(self.team.id), "name": self.team.name, "part_of_ecju": None},
        )

    @parameterized.expand(
        [
            [""],  # Blank
            ["test"],  # Case insensitive duplicate names
            [" TesT "],
            ["TEST"],
            ["a" * 21],  # Too long a name
        ]
    )
    def test_create_flag_failure(self, name):
        self.create_flag("test", FlagLevels.CASE, self.team)

        response = self.client.post(self.url, {"name": name}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_set_priority_to_less_than_0(self):
        data = {
            "name": "new flag",
            "level": "Organisation",
            "priority": -1,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(strings.Flags.ValidationErrors.PRIORITY_NEGATIVE, response_data["errors"]["priority"])

    def test_cannot_set_priority_to_greater_than_100(self):
        data = {
            "name": "new flag",
            "level": "Organisation",
            "priority": 101,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(strings.Flags.ValidationErrors.PRIORITY_TOO_LARGE, response_data["errors"]["priority"])

    def test_cannot_create_flag_with_colour_and_no_label(self):
        data = {
            "name": "new flag",
            "level": "Organisation",
            "colour": FlagColours.ORANGE,
            "label": "",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(strings.Flags.ValidationErrors.LABEL_MISSING, response.json()["errors"]["label"])

    def test_cannot_create_flag_without_blocks_finalising(self):
        data = {
            "name": "new flag",
            "level": "Organisation",
            "colour": FlagColours.ORANGE,
            "label": "This is label",
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["blocks_finalising"], [strings.Flags.ValidationErrors.BLOCKING_APPROVAL_MISSING]
        )
