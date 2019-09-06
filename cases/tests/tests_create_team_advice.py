from django.urls import reverse
from parameterized import parameterized

from cases.enums import AdviceType
from cases.models import Case
from cases.tests.tests_create_advice import CreateCaseAdviceTests
from test_helpers.clients import DataTestClient


class CreateCaseTeamAdviceTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.standard_case = Case.objects.get(application=self.standard_application)

        self.open_application = self.create_open_application(self.organisation)
        self.open_case = Case.objects.get(application=self.open_application)

        self.standard_case_url = reverse('cases:case_team_advice', kwargs={'pk': self.standard_case.id})
        self.open_case_url = reverse('cases:case_team_advice', kwargs={'pk': self.open_case.id})


# Normal restrictions on team advice items
    @parameterized.expand([
        [AdviceType.APPROVE],
        [AdviceType.PROVISO],
        [AdviceType.REFUSE],
        [AdviceType.NO_LICENCE_REQUIRED],
        [AdviceType.NOT_APPLICABLE],
    ])
    def test_create_end_user_case_team_advice(self, advice_type):
        """
        Tests that a gov user can create an approval/proviso/refuse/nlr/not_applicable
        piece of team level advice for an end user
        """
        CreateCaseAdviceTests.create_advice_base_test(self, advice_type, self.standard_case_url)

# User must have permission to create team advice
    def test_user_cannot_create_team_level_advice_without_permissions(self):
        pass

# LIST OF THINGS TO TEST
# If any team advice exists on case, unable to modify all user-belonging-to-that-team advice on that case
# If no team advice exists on case, able to modify all user-belonging-to-that-team advice on that case
# Create team advice with appropriate audit + timeline
# Edit and delete has some form of audit + timeline
