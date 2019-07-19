from django.urls import reverse

from cases.models import Case
from teams.models import Team
from queues.models import Queue
from test_helpers.clients import DataTestClient


class CaseFlagsManagementTests(DataTestClient):
    """
        Given I am a logged in government user viewing a case
        Then I should see any flags which are already set on the case including those which belong to other teams
        And I should see an option to edit the case flags

        When I choose to edit the case flags
        Then I should see only the case level flags which are set that belong to my team
        And I should see an option to set more flags
        And I should see an option to unset the existing flags

        When I choose to unset an existing flag
        Then  I should be able to remove a flag and no longer see it on the case

        When I choose to set more case flags
        Then I should see all the flags which belong to my team that are not already set on the case
        And I should be able to select one or more to add to the case
    """

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application',
                                                                               self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.default_queue = Queue.objects.get(id='00000000-0000-0000-0000-000000000001')
        self.default_team = Team.objects.get(id='00000000-0000-0000-0000-000000000001')

        # Cases
        self.case = Case.objects.get(application=self.application)

        # Teams
        self.other_team = self.create_team("Team")

        # Flags
        self.team_case_flag_1 = self.create_flag("Case Flag 1", "Case", self.team)
        self.team_org_flag_1 = self.create_flag("Org Flag 1", "Organisation", self.team)
        self.team_case_flag_2 = self.create_flag("Case Flag 2", "Case", self.team)
        self.other_team_case_flag = self.create_flag("Other Team Case Flag", "Case", self.other_team)
        self.all_flags = [self.team_case_flag_1, self.team_org_flag_1, self.team_case_flag_2, self.other_team_case_flag] 

        self.case_url = reverse('cases:case', kwargs={'pk': self.case.id})
        self.case_flag_url = reverse('cases:case_flags', kwargs={'pk': self.case.id})
        self.audit_url = reverse('cases:activity', kwargs={'pk': self.case.id}) + "?fields=flags"

    def test_correct_flags_returned_for_new_case(self):
        """
        Given a new case
        When a user requests case
        Then an empty list is returned
        """
        # Arrange

        # Act
        response = self.client.get(self.case_url, **self.gov_headers)

        # Assert
        self.assertEqual(response.json()['case']['flags'], [])

    def test_given_case_with_flags_then_flags_returned(self):
        """
        Given a Case
        And CaseFlags are already set
        When a user requests CaseFlags
        Then the correct flags are returned
        """
        # Arrange
        self.case.flags.set(self.all_flags)

        # Act
        response = self.client.get(self.case_url, **self.gov_headers)
        returned_case = response.json()['case']

        # Assert
        self.assertEquals(len(self.case.flags.all()), len(returned_case['flags']))

    # def test_given_new_case_when_case_is_on_users_queue_when_flags_are_set_then_they_are_returned_correctly(self):
    #     assert False

    # def test_given_new_case_when_case_is_on_users_queue_when_case_has_more_than_one_flag_and_one_is_removed_then_remaining_flags_are_returned(self):
    #     assert False

    # def test_given_new_case_when_not_in_a_teams_queue_then_user_cannot_add_flags_from_that_team(self):
    #     assert False
    #     # Expecting 401 bad-request

    # def test_given_new_case_when_case_is_on_queue_and_user_is_not_on_team_then_user_cannot_add_flags_from_that_team(self):
    #     assert False
    #     # Expecting 401 bad-request

    # def test_given_new_case_when_case_is_on_queue_then_user_is_not_allowed_toassig_a_flag_that_is_not_case_level(self):
    #     assert False
    #     # Expecting 401 bad-request

    def test_given_case_has_been_modified_then_appropriate_audit_is_in_place(self):
        """
        Given a new Case
        When a case-level flag is added
        Then an audit record is created
        """
        # Arrange
        flags = {'flags': [self.team_case_flag_1.pk]}

        # Act
        test = self.client.put(self.case_flag_url, flags, **self.gov_headers)
        response = self.client.get(self.audit_url, **self.gov_headers)

        # Assert
        response_data = response.json()
        activity = response_data['activity']
        self.assertEquals(len(activity), 1)
        self.assertEquals(activity[0]['data']['flags']['added'], [self.team_case_flag_1.__dict__['name']])
