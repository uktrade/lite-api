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

        # Flags
        self.flag1 = self.create_flag("Flag1", "Case", self.team)
        self.flag2 = self.create_flag("Flag2", "Organisation", self.team)
        self.flag3 = self.create_flag("Flag3", "Case", self.team)

        # Cases
        self.case = Case.objects.get(application=self.application)
        CaseFlags(case=self.case, flag=self.flag1).save()
        CaseFlags(case=self.case, flag=self.flag2).save()
        CaseFlags(case=self.case, flag=self.flag3).save()

        self.url = reverse('cases:case_flags', kwargs={'pk': self.case.id})

    def test_can_see_all_flags_on_case(self):
        response = self.client.get(self.url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(len(response_data['case_flags']), 3)
