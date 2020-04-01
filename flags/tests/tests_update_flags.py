from django.urls import reverse
from rest_framework import status

from flags.enums import FlagStatuses, FlagColours
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient


class FlagsUpdateTest(DataTestClient):
    def test_flag_can_be_deactivated(self):
        flag = self.create_flag("New Flag", "Case", self.team)

        data = {
            "status": FlagStatuses.DEACTIVATED,
        }

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.patch(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["status"], FlagStatuses.DEACTIVATED)

    def test_flag_cannot_be_deactivated_by_a_user_outside_flags_team(self):
        team = self.create_team("Secondary team")
        flag = self.create_flag("New Flag", "Case", team)

        data = {
            "status": FlagStatuses.DEACTIVATED,
        }

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(flag.status, FlagStatuses.ACTIVE)

    def test_flag_level_cannot_be_changed(self):
        team = self.create_team("Secondary team")
        flag = self.create_flag("New Flag", "Case", team)

        data = {
            "level": "Good",
        }

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        self.client.put(url, data, **self.gov_headers)

        self.assertEqual(flag.level, "Case")

    def test_colour_can_be_changed_from_default(self):
        flag = self.create_flag("New Flag", "Case", self.team)
        label_text = "This a label"

        data = {"colour": FlagColours.ORANGE, "label": label_text}

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.patch(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["colour"], FlagColours.ORANGE)
        self.assertEqual(response_data["label"], label_text)

    def test_colour_cannot_be_changed_from_default_without_adding_a_label(self):
        flag = self.create_flag("New Flag", "Case", self.team)

        data = {"colour": FlagColours.ORANGE, "label": ""}

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.patch(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(strings.Flags.ValidationErrors.LABEL_MISSING, response.json()["errors"]["label"])

        flag.refresh_from_db()
        self.assertEqual(flag.colour, FlagColours.DEFAULT)
        self.assertEqual(flag.label, None)

    def test_priority_can_be_updated(self):
        flag = self.create_flag("New Flag", "Case", self.team)

        data = {"priority": 1}

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.patch(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["priority"], 1)
