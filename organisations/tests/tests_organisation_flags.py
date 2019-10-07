from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class OrganisationFlagsManagementTests(DataTestClient):

    def setUp(self):
        super().setUp()
        # Teams
        self.other_team = self.create_team('Team')

        # Flags
        self.team_organisation_flag_1 = self.create_flag('Organisation Flag 1', 'Organisation', self.team)
        self.team_organisation_flag_2 = self.create_flag('Organisation Flag 2', 'Organisation', self.team)
        self.good_flag = self.create_flag('Good flag', 'Good', self.team)
        self.other_team_organisation_flag = self.create_flag('Other Team Organisation Flag', 'Organisation', self.other_team)
        self.all_flags = [self.team_organisation_flag_1, self.team_organisation_flag_2, self.other_team_organisation_flag]

        self.organisation_url = reverse('organisations:organisation', kwargs={'pk': self.organisation.id})
        self.organisation_flag_url = reverse('flags:assign_flags')

    def test_no_flags_for_organisation_are_returned(self):
        """
        Given a Organisation with no Flags assigned
        When a user requests the Organisation
        Then the correct Organisation with an empty Flag list is returned
        """

        response = self.client.get(self.organisation_url, **self.gov_headers)

        self.assertEqual([], response.json()['flags'])

    def test_all_flags_for_organisation_are_returned(self):
        """
        Given a Organisation with Flags already assigned
        When a user requests the Organisation
        Then the correct Organisation with all assigned Flags are returned
        """
        self.organisation.flags.set(self.all_flags)

        response = self.client.get(self.organisation_url, **self.gov_headers)
        returned_organisation = response.json()

        self.assertEquals(len(self.organisation.flags.all()), len(returned_organisation['flags']))

    def test_user_can_add_organisation_level_flags_from_their_own_team(self):
        """
        Given a Organisation with no Flags assigned
        When a user attempts to add a organisation-level Flag owned by their Team to the Organisation
        Then the Flag is successfully added
        """
        data = {
            'level': 'organisations',
            'objects': [self.organisation.pk],
            'flags': [self.team_organisation_flag_1.pk],
            'note': 'A reason for changing the flags'
        }

        self.client.put(self.organisation_flag_url, data, **self.gov_headers)

        self.assertEquals(len(data['flags']), len(self.organisation.flags.all()))
        self.assertTrue(self.team_organisation_flag_1 in self.organisation.flags.all())

    def test_user_cannot_assign_flags_that_are_not_owned_by_their_team(self):
        """
        Given a Organisation with no Flags assigned
        When a user attempts to add a organisation-level Flag not owned by their Team to the Organisation
        Then the Flag is not added
        """
        data = {
            'level': 'organisations',
            'objects': [self.organisation.pk],
            'flags': [self.other_team_organisation_flag.pk],
            'note': 'A reason for changing the flags'
        }

        response = self.client.put(self.organisation_flag_url, data, **self.gov_headers)

        self.assertEquals(0, len(self.organisation.flags.all()))
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_user_cannot_assign_flags_that_are_not_organisation_level(self):
        """
        Given a Organisation with no Flags assigned
        When a user attempts to add a non-organisation-level Flag owned by their Team to the Organisation
        Then the Flag is not added
        """
        data = {
            'level': 'organisations',
            'objects': [self.organisation.pk],
            'flags': [self.good_flag.id],
            'note': 'A reason for changing the flags'
        }

        response = self.client.put(self.organisation_flag_url, data, **self.gov_headers)

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEquals(0, len(self.organisation.flags.all()))

    def test_when_one_flag_is_removed_then_other_flags_are_unaffected(self):
        """
        Given a Organisation with Flags already assigned
        When a user removes a organisation-level Flag owned by their Team from the Organisation
        Then only that Flag is removed
        """
        self.all_flags.remove(self.team_organisation_flag_1)
        self.organisation.flags.set(self.all_flags)
        data = {
            'level': 'organisations',
            'objects': [self.organisation.pk],
            'flags': [self.team_organisation_flag_2.pk],
            'note': 'A reason for changing the flags'
        }

        self.client.put(self.organisation_flag_url, data, **self.gov_headers)

        self.assertEquals(len(self.all_flags), len(self.organisation.flags.all()))
        for flag in self.all_flags:
            self.assertTrue(flag in self.organisation.flags.all())

    # TODO: Establish stable activity for organisation avoiding circular imports
    # def test_flagging_a_organisation_creates_timeline_entries(self):
    #     """
    #     When a user adds a flag to a organisation, it should add a timeline entry
    #     to whatever case that organisation is on (if any)
    #     """
    #     # Set the query and application's organisation
    #
    #     data = {
    #         'level': 'organisations',
    #         'objects': [self.organisation.pk],
    #         'flags': [self.team_organisation_flag_1.pk],
    #         'note': 'A reason for changing the flags'
    #     }
    #
    #     self.client.put(self.organisation_flag_url, data, **self.gov_headers)
