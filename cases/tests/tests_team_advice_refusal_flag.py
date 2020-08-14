from rest_framework.reverse import reverse

from cases.enums import AdviceType, AdviceLevel
from cases.libraries.post_advice import case_advice_contains_refusal
from cases.models import Case
from api.conf import constants
from flags.enums import SystemFlags
from flags.models import Flag
from test_helpers.clients import DataTestClient
from api.users.models import Role


class CasesFilterAndSortTests(DataTestClient):
    def _check_if_flag_exists(self):
        self.standard_case = Case.objects.get(id=self.standard_case.id)
        flag = Flag.objects.get(id=SystemFlags.REFUSAL_FLAG_ID)
        return flag in self.standard_case.flags.all()

    def setUp(self):
        super().setUp()

        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.standard_case = self.submit_application(self.standard_application)

        role = Role(name="team_level")
        role.permissions.set([constants.GovPermissions.MANAGE_TEAM_CONFIRM_OWN_ADVICE.name])
        role.save()

        self.gov_user.role = role
        self.gov_user.save()

        self.url = reverse("cases:team_advice", kwargs={"pk": self.standard_case.id})

    def test_combine_user_refusal_creates_flag(self):
        self.create_advice(self.gov_user, self.standard_case, "end_user", AdviceType.REFUSE, AdviceLevel.USER)

        self.assertFalse(self._check_if_flag_exists())

        self.client.get(self.url, **self.gov_headers)

        self.assertTrue(self._check_if_flag_exists())

    def test_clear_advice_back_to_user_level_removes_flag(self):
        self.create_advice(self.gov_user, self.standard_case, "end_user", AdviceType.REFUSE, AdviceLevel.TEAM)

        self.client.delete(self.url, **self.gov_headers)

        self.assertFalse(self._check_if_flag_exists())

    # tests the function (case_advice_contains_refusal) which this is all based around
    def test_team_advice_contains_refusal_true(self):
        self.create_advice(self.gov_user, self.standard_case, "end_user", AdviceType.REFUSE, AdviceLevel.TEAM)
        case_advice_contains_refusal(self.standard_case.id)

        self.assertTrue(self._check_if_flag_exists())

    def test_team_advice_contains_refusal_false(self):
        self.create_advice(self.gov_user, self.standard_case, "end_user", AdviceType.PROVISO, AdviceLevel.TEAM)
        case_advice_contains_refusal(self.standard_case.id)

        self.assertFalse(self._check_if_flag_exists())
