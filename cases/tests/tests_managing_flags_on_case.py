from django.urls import reverse
from rest_framework import status

from cases.models import Case
from queues.models import Queue
from teams.models import Team
from test_helpers.clients import DataTestClient


class CaseFlagsManagementTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.exporter_user.organisation)
        self.default_queue = Queue.objects.get(id='00000000-0000-0000-0000-000000000001')
        self.default_team = Team.objects.get(id='00000000-0000-0000-0000-000000000001')

        # Cases
        self.case = Case.objects.get(application=self.standard_application)

        # Teams
        self.other_team = self.create_team('Team')

        # Flags
        self.team_case_flag_1 = self.create_flag('Case Flag 1', 'Case', self.team)
        self.team_case_flag_2 = self.create_flag('Case Flag 2', 'Case', self.team)
        self.team_org_flag = self.create_flag('Org Flag 1', 'Organisation', self.team)
        self.other_team_case_flag = self.create_flag('Other Team Case Flag', 'Case', self.other_team)
        self.all_flags = [self.team_case_flag_1, self.team_org_flag, self.team_case_flag_2, self.other_team_case_flag]

        self.case_url = reverse('cases:case', kwargs={'pk': self.case.id})
        self.case_flag_url = reverse('cases:case_flags', kwargs={'pk': self.case.id})
        self.audit_url = reverse('cases:activity', kwargs={'pk': self.case.id}) + '?fields=flags'

    def test_no_flags_for_case_are_returned(self):
        """
        Given a Case with no Flags assigned
        When a user requests the Case
        Then the correct Case with an empty Flag list is returned
        """

        # Arrange

        # Act
        response = self.client.get(self.case_url, **self.gov_headers)

        # Assert
        self.assertEqual([], response.json()['case']['flags'])

    def test_all_flags_for_case_are_returned(self):
        """
        Given a Case with Flags already assigned
        When a user requests the Case
        Then the correct Case with all assigned Flags are returned
        """

        # Arrange
        self.case.flags.set(self.all_flags)

        # Act
        response = self.client.get(self.case_url, **self.gov_headers)
        returned_case = response.json()['case']

        # Assert
        self.assertEquals(len(self.case.flags.all()), len(returned_case['flags']))

    def test_user_can_add_case_level_flags_from_their_own_team(self):
        """
        Given a Case with no Flags assigned
        When a user attempts to add a case-level Flag owned by their Team to the Case
        Then the Flag is successfully added
        """

        # Arrange
        flags_to_add = {'flags': [self.team_case_flag_1.pk]}

        # Act
        self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        # Assert
        self.assertEquals(len(flags_to_add['flags']), len(self.case.flags.all()))
        self.assertTrue(self.team_case_flag_1 in self.case.flags.all())

    def test_user_cannot_assign_flags_that_are_not_owned_by_their_team(self):
        """
        Given a Case with no Flags assigned
        When a user attempts to add a case-level Flag not owned by their Team to the Case
        Then the Flag is not added
        """

        # Arrange
        flags_to_add = {'flags': [self.other_team_case_flag.pk]}

        # Act
        response = self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        # Assert
        self.assertEquals(0, len(self.case.flags.all()))
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_user_cannot_assign_flags_that_are_not_case_level(self):
        """
        Given a Case with no Flags assigned
        When a user attempts to add a non-case-level Flag owned by their Team to the Case
        Then the Flag is not added
        """

        # Arrange
        flags_to_add = {'flags': [self.team_org_flag.pk]}

        # Act
        response = self.client.put(self.case_flag_url, flags_to_add, **self.gov_headers)

        # Assert
        self.assertEquals(0, len(self.case.flags.all()))
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_when_one_flag_is_removed_then_other_flags_are_unaffected(self):
        """
        Given a Case with Flags already assigned
        When a user removes a case-level Flag owned by their Team from the Case
        Then only that Flag is removed
        """

        # Arrange (note that the endpoint expects flags being PUT to the case, therefore the flag being removed is not
        # included in the request body)
        self.case.flags.set(self.all_flags)
        flags_to_keep = {'flags': [self.team_case_flag_2.pk]}
        self.all_flags.remove(self.team_case_flag_1)

        # Act
        self.client.put(self.case_flag_url, flags_to_keep, **self.gov_headers)

        # Assert
        self.assertEquals(len(self.all_flags), len(self.case.flags.all()))
        for flag in self.all_flags:
            self.assertTrue(flag in self.case.flags.all())

    def test_given_case_has_been_modified_then_appropriate_audit_is_in_place(self):
        """
        Given a Case with no Flags assigned
        When a user attempts to add a non-case-level Flag owned by their Team to the Case
        And the Flag is successfully added
        And an audit record is created
        And the user requests the activity on the Case
        Then the activity is returned showing the Flag which was added
        """

        # Arrange
        flags = {'flags': [self.team_case_flag_1.pk]}

        # Act
        self.client.put(self.case_flag_url, flags, **self.gov_headers)
        response = self.client.get(self.audit_url, **self.gov_headers)

        # Assert
        response_data = response.json()
        activity = response_data['activity']
        self.assertEquals(len(flags['flags']), len(activity))
        self.assertEquals([self.team_case_flag_1.__dict__['name']], activity[0]['data']['flags']['added'])
