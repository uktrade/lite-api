from django.urls import reverse
from rest_framework import status

from queues.models import Queue
from teams.models import Team
from test_helpers.clients import DataTestClient


class GoodFlagsManagementTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.exporter_user.organisation)
        self.default_queue = Queue.objects.get(id='00000000-0000-0000-0000-000000000001')
        self.default_team = Team.objects.get(id='00000000-0000-0000-0000-000000000001')

        # Cases
        self.good = self.create_controlled_good('a good', self.organisation)

        # Teams
        self.other_team = self.create_team('Team')

        # Flags
        self.team_good_flag_1 = self.create_flag('Good Flag 1', 'Good', self.team)
        self.team_good_flag_2 = self.create_flag('Good Flag 2', 'Good', self.team)
        self.team_org_flag = self.create_flag('Org Flag 1', 'Organisation', self.team)
        self.other_team_good_flag = self.create_flag('Other Team Good Flag', 'Good', self.other_team)
        self.all_flags = [self.team_good_flag_1, self.team_org_flag, self.team_good_flag_2, self.other_team_good_flag]

        self.good_url = reverse('goods:good', kwargs={'pk': self.good.id})
        self.good_flag_url = reverse('goods:good_flags', kwargs={'pk': self.good.id})
        self.audit_url = reverse('goods:activity', kwargs={'pk': self.good.id})

    def test_no_flags_for_good_are_returned(self):
        """
        Given a Good with no Flags assigned
        When a user requests the Good
        Then the correct Good with an empty Flag list is returned
        """

        # Arrange

        # Act
        response = self.client.get(self.good_url, **self.gov_headers)

        # Assert
        self.assertEqual([], response.json()['good']['flags'])

    def test_all_flags_for_good_are_returned(self):
        """
        Given a Good with Flags already assigned
        When a user requests the Good
        Then the correct Good with all assigned Flags are returned
        """

        # Arrange
        self.good.flags.set(self.all_flags)

        # Act
        response = self.client.get(self.good_url, **self.gov_headers)
        returned_good = response.json()['good']

        # Assert
        self.assertEquals(len(self.good.flags.all()), len(returned_good['flags']))

    def test_user_can_add_good_level_flags_from_their_own_team(self):
        """
        Given a Good with no Flags assigned
        When a user attempts to add a good-level Flag owned by their Team to the Good
        Then the Flag is successfully added
        """

        # Arrange
        flags_to_add = {'flags': [self.team_good_flag_1.pk], 'note': 'A reason for changing the flags'}

        # Act
        self.client.put(self.good_flag_url, flags_to_add, **self.gov_headers)

        # Assert
        self.assertEquals(len(flags_to_add['flags']), len(self.good.flags.all()))
        self.assertTrue(self.team_good_flag_1 in self.good.flags.all())

    def test_user_cannot_assign_flags_that_are_not_owned_by_their_team(self):
        """
        Given a Good with no Flags assigned
        When a user attempts to add a good-level Flag not owned by their Team to the Good
        Then the Flag is not added
        """

        # Arrange
        flags_to_add = {'flags': [self.other_team_good_flag.pk], 'note': 'A reason for changing the flags'}

        # Act
        response = self.client.put(self.good_flag_url, flags_to_add, **self.gov_headers)

        # Assert
        self.assertEquals(0, len(self.good.flags.all()))
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_user_cannot_assign_flags_that_are_not_good_level(self):
        """
        Given a Good with no Flags assigned
        When a user attempts to add a non-good-level Flag owned by their Team to the Good
        Then the Flag is not added
        """

        # Arrange
        flags_to_add = {'flags': [self.team_org_flag.pk], 'note': 'A reason for changing the flags'}

        # Act
        response = self.client.put(self.good_flag_url, flags_to_add, **self.gov_headers)

        # Assert
        self.assertEquals(0, len(self.good.flags.all()))
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_when_one_flag_is_removed_then_other_flags_are_unaffected(self):
        """
        Given a Good with Flags already assigned
        When a user removes a good-level Flag owned by their Team from the Good
        Then only that Flag is removed
        """

        # Arrange (note that the endpoint expects flags being PUT to the good, therefore the flag being removed is not
        # included in the request body)
        self.all_flags.remove(self.team_org_flag)
        self.good.flags.set(self.all_flags)
        flags_to_keep = {'flags': [self.team_good_flag_2.pk], 'note': 'A reason for changing the flags'}
        self.all_flags.remove(self.team_good_flag_1)

        # Act
        self.client.put(self.good_flag_url, flags_to_keep, **self.gov_headers)

        # Assert
        self.assertEquals(len(self.all_flags), len(self.good.flags.all()))
        for flag in self.all_flags:
            self.assertTrue(flag in self.good.flags.all())

    def test_given_good_has_been_modified_then_appropriate_audit_is_in_place(self):
        """
        Given a Good with no Flags assigned
        When a user attempts to add a non-good-level Flag owned by their Team to the Good
        And the Flag is successfully added
        And an audit record is created
        And the user requests the activity on the Good
        Then the activity is returned showing the Flag which was added
        """

        # Arrange
        flags = {'flags': [self.team_good_flag_1.pk], 'note': 'A reason for changing the flags'}

        # Act
        self.client.put(self.good_flag_url, flags, **self.gov_headers)
        response = self.client.get(self.audit_url, **self.gov_headers)

        # Assert
        response_data = response.json()
        activity = response_data['activity']
        self.assertEquals(len(flags['flags']), len(activity))
        self.assertEquals([self.team_good_flag_1.__dict__['name']], activity[0]['data']['flags']['added'])
