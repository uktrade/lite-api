from django.core.management import call_command
from rest_framework.reverse import reverse

from cases.enums import AdviceType
from cases.libraries.post_advice import case_advice_contains_refusal
from cases.models import Case, Advice, TeamAdvice
from conf.constants import Permissions
from flags.enums import SystemFlags
from flags.models import Flag
from test_helpers.clients import DataTestClient
from users.models import Role


class CasesFilterAndSortTests(DataTestClient):

    def check_if_flag_exists(self):
        self.standard_case = Case.objects.get(application=self.standard_application)
        flag = Flag.objects.get(id=SystemFlags.REFUSAL_FLAG_ID)
        return flag in self.standard_case.flags.all()

    def setUp(self):
        super().setUp()
        # seed system flags
        call_command('seedsystemflags')

        self.standard_application = self.create_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.standard_case = Case.objects.get(application=self.standard_application)

        role = Role(name='team_level')
        role.permissions.set([Permissions.MANAGE_TEAM_ADVICE])
        role.save()

        self.gov_user.role = role
        self.gov_user.save()

    def test_combine_user_refusal_creates_flag(self):
        self.create_advice(self.gov_user, self.standard_case, 'end_user', AdviceType.REFUSE, Advice)
        assert not self.check_if_flag_exists()

        url = reverse('cases:case_team_advice', kwargs={'pk': self.standard_case.id})

        self.client.get(url, **self.gov_headers)

        assert self.check_if_flag_exists()

    def test_clear_advice_back_to_user_level_removes_flag(self):
        self.create_advice(self.gov_user, self.standard_case, 'end_user', AdviceType.REFUSE, TeamAdvice)

        url = reverse('cases:case_team_advice', kwargs={'pk': self.standard_case.id})

        self.client.delete(url, **self.gov_headers)

        assert not self.check_if_flag_exists()

    # tests the function (case_advice_contains_refusal) which this is all based around
    def test_team_advice_contains_refusal_true(self):
        self.create_advice(self.gov_user, self.standard_case, 'end_user', AdviceType.REFUSE, TeamAdvice)
        case_advice_contains_refusal(self.standard_case.id)
        assert self.check_if_flag_exists()

    def test_team_advice_contains_refusal_false(self):
        self.create_advice(self.gov_user, self.standard_case, 'end_user', AdviceType.PROVISO, TeamAdvice)
        case_advice_contains_refusal(self.standard_case.id)
        assert not self.check_if_flag_exists()
