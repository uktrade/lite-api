from django.urls import reverse
from rest_framework import status

from parties.enums import PartyType
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class PartyFlagsManagementTests(DataTestClient):
    def setUp(self):
        super().setUp()
        # Destinations
        name = "a name"
        organisation = self.organisation
        application = self.create_standard_application(organisation=organisation)
        self.end_user = self.create_party(name, organisation, PartyType.END_USER, application)
        self.ultimate_end_user = self.create_party(name, organisation, PartyType.ULTIMATE_END_USER, application)
        self.consignee = self.create_party(name, organisation, PartyType.CONSIGNEE, application)
        self.third_party = self.create_party(name, organisation, PartyType.THIRD_PARTY, application)

        # Teams
        self.other_team = self.create_team("Team")

        # Flags
        self.team_destination_flag_1 = self.create_flag("Destination Flag 1", "Destination", self.team)
        self.team_destination_flag_2 = self.create_flag("Destination Flag 2", "Destination", self.team)
        self.team_org_flag = self.create_flag("Org Flag 1", "Organisation", self.team)
        self.other_team_destination_flag = self.create_flag(
            "Other Team Destination Flag", "Destination", self.other_team
        )
        self.all_flags = [
            self.team_destination_flag_1,
            self.team_org_flag,
            self.team_destination_flag_2,
            self.other_team_destination_flag,
        ]

        self.assign_flag_url = reverse("flags:assign_flags")

    def test_user_can_add_destination_level_flags_from_their_own_team(self):
        """
        Given a Good with no Flags assigned
        When a user attempts to add a good-level Flag owned by their Team to the Good
        Then the Flag is successfully added
        """
        country = get_country("XQZ")
        data = {
            "level": "destinations",
            "objects": [
                self.end_user.pk,
                self.ultimate_end_user.pk,
                self.consignee.pk,
                self.third_party.pk,
                country.id,
            ],
            "flags": [self.team_destination_flag_1.pk],
            "note": "A reason for changing the flags",
        }

        self.client.put(self.assign_flag_url, data, **self.gov_headers)

        self.assertEquals(len(data["flags"]), len(self.end_user.flags.all()))
        self.assertTrue(self.team_destination_flag_1 in self.end_user.flags.all())
        self.assertEquals(len(data["flags"]), len(self.ultimate_end_user.flags.all()))
        self.assertTrue(self.team_destination_flag_1 in self.ultimate_end_user.flags.all())
        self.assertEquals(len(data["flags"]), len(self.consignee.flags.all()))
        self.assertTrue(self.team_destination_flag_1 in self.consignee.flags.all())
        self.assertEquals(len(data["flags"]), len(self.third_party.flags.all()))
        self.assertTrue(self.team_destination_flag_1 in self.third_party.flags.all())
        self.assertEquals(len(data["flags"]), len(country.flags.all()))
        self.assertTrue(self.team_destination_flag_1 in country.flags.all())

    def test_user_cannot_assign_flags_that_are_not_owned_by_their_team(self):
        """
        Given a Good with no Flags assigned
        When a user attempts to add a good-level Flag not owned by their Team to the Good
        Then the Flag is not added
        """
        data = {
            "level": "destinations",
            "objects": [self.end_user.pk],
            "flags": [self.other_team_destination_flag.pk],
            "note": "A reason for changing the flags",
        }

        response = self.client.put(self.assign_flag_url, data, **self.gov_headers)

        self.assertEquals(0, len(self.end_user.flags.all()))
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_user_cannot_assign_flags_that_are_not_destination_level(self):
        """
        Given a Good with no Flags assigned
        When a user attempts to add a non-good-level Flag owned by their Team to the Good
        Then the Flag is not added
        """
        data = {
            "level": "destinations",
            "objects": [self.end_user.pk],
            "flags": [self.team_org_flag.pk],
            "note": "A reason for changing the flags",
        }

        response = self.client.put(self.assign_flag_url, data, **self.gov_headers)

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEquals(0, len(self.end_user.flags.all()))

    def test_when_one_flag_is_removed_then_other_flags_are_unaffected(self):
        """
        Given a Good with Flags already assigned
        When a user removes a good-level Flag owned by their Team from the Good
        Then only that Flag is removed
        """
        self.all_flags.remove(self.team_org_flag)
        self.end_user.flags.set(self.all_flags)
        data = {
            "level": "destinations",
            "objects": [self.end_user.pk],
            "flags": [self.team_destination_flag_2.pk],
            "note": "A reason for changing the flags",
        }
        self.all_flags.remove(self.team_destination_flag_1)

        self.client.put(self.assign_flag_url, data, **self.gov_headers)

        self.assertEquals(len(self.all_flags), len(self.end_user.flags.all()))
        for flag in self.all_flags:
            self.assertTrue(flag in self.end_user.flags.all())

    def test_setting_flags_on_two_parties(self):
        """
        Tests setting multiple flags on multiple goods types simultaneously
        """
        data = {
            "level": "destinations",
            "objects": [self.end_user.id, self.ultimate_end_user.id],
            "flags": [self.team_destination_flag_1.pk, self.team_destination_flag_2.pk],
            "note": "A reason for changing the flags",
        }

        response = self.client.put(self.assign_flag_url, data, **self.gov_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 2)

    # TODO: Complete when new activity stream is in place
    # def test_flagging_a_good_creates_timeline_entries(self):
    #     """
    #     When a user adds a flag to a good, it should add a timeline entry
    #     to whatever case that good is on (if any)
    #     """
    #     query = self.create_clc_query("Query", self.organisation)
    #
    #     # Set the query and application's good
    #     query.good = self.good
    #     query.save()
    #
    #     data = {
    #         "level": "goods",
    #         "objects": [self.good.pk],
    #         "flags": [self.team_good_flag_1.pk],
    #         "note": "A reason for changing the flags",
    #     }
    #
    #     self.client.put(self.assign_flag_url, data, **self.gov_headers)
    #
    #     self.assertEqual(len(get_case_activity(Case.objects.get(id=query.id))), 1)
