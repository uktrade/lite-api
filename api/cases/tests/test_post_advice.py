from rest_framework.reverse import reverse

from api.cases.enums import AdviceType, AdviceLevel
from api.cases.libraries.post_advice import update_advice_completed_flag
from api.cases.models import Case
from api.core import constants
from api.flags.enums import SystemFlags
from api.flags.models import Flag
from test_helpers.clients import DataTestClient
from api.users.models import Role


class AdviceCompletedTests(DataTestClient):

    def _check_if_flag_exists(self):
        flag = Flag.objects.get(id=SystemFlags.ADVICE_COMPLETED_ID)
        return flag in self.standard_case.flags.all()

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.standard_case = self.submit_application(self.standard_application)

    def test_update_advice_creates_flag(self):
        self.create_advice(self.gov_user, self.standard_case, "end_user", AdviceType.APPROVE, AdviceLevel.USER)
        self.assertFalse(self._check_if_flag_exists())
        update_advice_completed_flag(self.standard_case)
