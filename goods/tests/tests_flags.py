from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status

from audit_trail.models import Audit
from cases.models import Case
from flags.enums import SystemFlags
from flags.models import Flag
from test_helpers.clients import DataTestClient


class GoodFlagsManagementTests(DataTestClient):
    def setUp(self):
        super().setUp()
        # Goods
        self.good = self.create_good("a good", self.organisation)
        self.good_2 = self.create_good("a second good", self.organisation)

        # Teams
        self.other_team = self.create_team("Team")

        # Flags
        self.team_good_flag_1 = self.create_flag("Good Flag 1", "Good", self.team)
        self.team_good_flag_2 = self.create_flag("Good Flag 2", "Good", self.team)
        self.team_org_flag = self.create_flag("Org Flag 1", "Organisation", self.team)
        self.other_team_good_flag = self.create_flag("Other Team Good Flag", "Good", self.other_team)
        self.all_flags = [
            self.team_good_flag_1,
            self.team_org_flag,
            self.team_good_flag_2,
            self.other_team_good_flag,
        ]

        self.good_url = reverse("goods:good", kwargs={"pk": self.good.id})
        self.good_flag_url = reverse("flags:assign_flags")

    def test_only_not_yet_verified_system_flag_for_good_is_returned(self):
        """
        Given a Good with no user-assigned Flags assigned
        When a user requests the Good
        Then the correct Good with only the 'not yet verified' Flag is returned
        """

        response = self.client.get(self.good_url, **self.gov_headers)

        self.assertEqual(len(response.json()["good"]["flags"]), 0)

    def test_all_flags_for_good_are_returned(self):
        """
        Given a Good with Flags already assigned
        When a user requests the Good
        Then the correct Good with all assigned Flags are returned
        """
        self.good.flags.set(self.all_flags)

        response = self.client.get(self.good_url, **self.gov_headers)
        returned_good = response.json()["good"]

        self.assertEquals(len(self.good.flags.all()), len(returned_good["flags"]))

    def test_user_can_add_good_level_flags_from_their_own_team(self):
        """
        Given a Good with no user-assigned Flags
        When a user attempts to add a good-level Flag owned by their Team to the Good
        Then the Flag is successfully added
        """
        previous_flag_count = self.good.flags.count()
        data = {
            "level": "goods",
            "objects": [self.good.pk],
            "flags": [self.team_good_flag_1.pk],
            "note": "A reason for changing the flags",
        }

        self.client.put(self.good_flag_url, data, **self.gov_headers)

        self.assertEquals(len(data["flags"]), 1)  # the PUT response data only includes flags that were added
        self.assertEquals(self.good.flags.count(), previous_flag_count + 1)
        self.assertTrue(self.team_good_flag_1 in self.good.flags.all())

    def test_user_cannot_assign_flags_that_are_not_owned_by_their_team(self):
        """
        Given a Good with no user-assigned Flags
        When a user attempts to add a good-level Flag not owned by their Team to the Good
        Then the Flag is not added
        """
        data = {
            "level": "goods",
            "objects": [self.good.pk],
            "flags": [self.other_team_good_flag.pk],
            "note": "A reason for changing the flags",
        }

        response = self.client.put(self.good_flag_url, data, **self.gov_headers)

        self.assertEquals(0, len(self.good.flags.all()))
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_user_cannot_assign_flags_that_are_not_good_level(self):
        """
        Given a Good with no user-assigned Flags
        When a user attempts to add a non-good-level Flag owned by their Team to the Good
        Then the Flag is not added
        """
        data = {
            "level": "goods",
            "objects": [self.good.pk],
            "flags": [self.team_org_flag.pk],
            "note": "A reason for changing the flags",
        }

        response = self.client.put(self.good_flag_url, data, **self.gov_headers)

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEquals(0, len(self.good.flags.all()))

    def test_when_one_flag_is_removed_then_other_flags_are_unaffected(self):
        """
        Given a Good with Flags already assigned
        When a user removes a good-level Flag owned by their Team from the Good
        Then only that Flag is removed
        """
        self.all_flags.remove(self.team_org_flag)
        self.good.flags.set(self.all_flags)
        data = {
            "level": "goods",
            "objects": [self.good.pk],
            "flags": [self.team_good_flag_2.pk],
            "note": "A reason for changing the flags",
        }
        self.all_flags.remove(self.team_good_flag_1)

        self.client.put(self.good_flag_url, data, **self.gov_headers)

        self.assertEquals(len(self.all_flags), len(self.good.flags.all()))
        for flag in self.all_flags:
            self.assertTrue(flag in self.good.flags.all())

    def test_setting_flags_on_two_goods(self):
        """
        Tests setting multiple flags on multiple goods types simultaneously
        """
        data = {
            "level": "goods",
            "objects": [self.good.id, self.good_2.id],
            "flags": [self.team_good_flag_2.pk, self.team_good_flag_1.pk],
            "note": "A reason for changing the flags",
        }

        response = self.client.put(self.good_flag_url, data, **self.gov_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 2)

    def test_flagging_a_good_creates_timeline_entries(self):
        """
        When a user adds a flag to a good, it should add a timeline entry
        to whatever case that good is on (if any)
        """
        query = self.create_clc_query("Query", self.organisation)

        # Set the query and application's good
        query.good = self.good
        query.save()

        data = {
            "level": "goods",
            "objects": [self.good.pk],
            "flags": [self.team_good_flag_1.pk],
            "note": "A reason for changing the flags",
        }

        self.client.put(self.good_flag_url, data, **self.gov_headers)

        case = Case.objects.get(id=query.id)

        audit_qs = Audit.objects.filter(
            target_object_id=case.id, target_content_type=ContentType.objects.get_for_model(case)
        )

        self.assertEqual(audit_qs.count(), 1)
