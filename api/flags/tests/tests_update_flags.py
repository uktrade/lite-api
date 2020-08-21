from django.urls import reverse
from rest_framework import status

from api.core.constants import GovPermissions
from api.flags.enums import FlagStatuses, FlagColours, FlagLevels
from api.flags.tests.factories import FlagFactory
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient


class FlagsUpdateTest(DataTestClient):
    def test_flag_can_be_deactivated(self):
        self.gov_user.role.permissions.set([GovPermissions.ACTIVATE_FLAGS.name])
        flag = FlagFactory(team=self.team)

        data = {
            "status": FlagStatuses.DEACTIVATED,
        }

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.patch(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["status"], FlagStatuses.DEACTIVATED)

    def test_flag_cannot_be_deactivated_without_permission(self):
        flag = FlagFactory(team=self.team)
        data = {
            "status": FlagStatuses.DEACTIVATED,
        }

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.patch(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_flag_cannot_be_deactivated_by_a_user_outside_flags_team(self):
        team = self.create_team("Secondary team")
        flag = FlagFactory(team=team)

        data = {
            "status": FlagStatuses.DEACTIVATED,
        }

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(flag.status, FlagStatuses.ACTIVE)

    def test_flag_level_cannot_be_changed(self):
        team = self.create_team("Secondary team")
        flag = FlagFactory(team=team, level=FlagLevels.CASE)

        data = {
            "level": "Good",
        }

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        self.client.put(url, data, **self.gov_headers)

        self.assertEqual(flag.level, "Case")

    def test_colour_can_be_changed_from_default(self):
        flag = FlagFactory(team=self.team)
        label_text = "This a label"

        data = {"colour": FlagColours.ORANGE, "label": label_text}

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.patch(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["colour"], FlagColours.ORANGE)
        self.assertEqual(response_data["label"], label_text)

    def test_colour_cannot_be_changed_from_default_without_adding_a_label(self):
        flag = FlagFactory(team=self.team)

        data = {"colour": FlagColours.ORANGE, "label": ""}

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.patch(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(strings.Flags.ValidationErrors.LABEL_MISSING, response.json()["errors"]["label"])

        flag.refresh_from_db()
        self.assertEqual(flag.colour, FlagColours.DEFAULT)
        self.assertEqual(flag.label, None)

    def test_priority_can_be_updated(self):
        flag = FlagFactory(team=self.team)

        data = {"priority": 1}

        url = reverse("flags:flag", kwargs={"pk": flag.id})
        response = self.client.patch(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["priority"], 1)
