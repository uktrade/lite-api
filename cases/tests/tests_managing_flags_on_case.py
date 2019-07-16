import json

from django.urls import reverse
from rest_framework import status

from cases.models import Case, CaseAssignment, CaseFlags
from teams.models import Team
from queues.models import Queue
from test_helpers.clients import DataTestClient


class CaseFlagsManagementTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application',
                                                                               self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.default_queue = Queue.objects.get(id='00000000-0000-0000-0000-000000000001')
        self.default_team = Team.objects.get(id='00000000-0000-0000-0000-000000000001')

        # # Flags
        # self.flag1 = self.create_flag("Flag1", "Case", self.team)
        # self.flag2 = self.create_flag("Flag2", "Organisation", self.team)
        # self.flag3 = self.create_flag("Flag3", "Case", self.team)

        # Cases
        # self.case = Case.objects.get(application=self.application)
        # CaseFlags(case=self.case, flag=self.flag1).save()
        # CaseFlags(case=self.case, flag=self.flag2).save()
        # CaseFlags(case=self.case, flag=self.flag3).save()

    # def test_can_see_all_flags_on_case(self):
    #     response = self.client.get(self.url, **self.gov_headers)

    #     response_data = response.json()

    #     self.assertEqual(len(response_data['case_flags']), 3)

    def test_given_new_case_then_return_flags_as_empty_list(self):
        case = Case.objects.get(application=self.application)
        url = reverse('cases:case_flags', kwargs={'pk': case.id})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.json()['case_flags'], [])
        case.delete()

    def test_given_case_with_flags_then_flags_returned(self):
        assert False

    def test_given_new_case_when_case_is_on_users_queue_when_flags_are_set_then_they_are_returned_correctly(self):
        assert False
    
    def test_given_new_case_when_case_is_on_users_queue_when_case_has_more_than_one_flag_and_one_is_removed_then_remaining_flags_are_returned(self):
        assert False

    def test_given_new_case_when_not_in_a_teams_queue_then_user_cannot_add_flags_from_that_team(self):
        assert False
        # Expecting 401 bad-request

    def test_given_new_case_when_case_is_on_queue_and_user_is_not_on_team_then_user_cannot_add_flags_from_that_team(self):
        assert False
        # Expecting 401 bad-request

    def test_given_new_case_when_case_is_on_queue_then_user_is_not_allowed_toassig_a_flag_that_is_not_case_level(self):
        assert False
        # Expecting 401 bad-request

    def test_given_case_has_been_modified_then_appropriate_audit_is_in_place(self):
        assert False
