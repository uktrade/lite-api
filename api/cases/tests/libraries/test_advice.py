from api.cases.enums import AdviceType
from api.cases.libraries import advice
from api.cases.tests import factories
from api.users.tests.factories import GovUserFactory
from api.teams.tests.factories import TeamFactory

from test_helpers.clients import DataTestClient


class TestAdviceHelpers(DataTestClient):
    def test_group_advice_single_approve(self):
        # given there is a case
        case = self.create_standard_application_case(self.organisation)
        good = self.create_good("A good", self.organisation)

        # and the case has a single approve
        factories.UserAdviceFactory.create(type=AdviceType.APPROVE, case=case, user=self.gov_user, good=good)

        advice_queryset = case.advice.all()
        # when the advice is collated
        advice.group_advice(
            case=case, advice=advice_queryset, user=self.base_user, new_level="team",
        )

        # then there is no conflict
        case.refresh_from_db()
        self.assertEqual(case.advice.all().count(), 2)
        self.assertEqual(case.advice.all().get(level="team").type, AdviceType.APPROVE)

    def test_group_advice_multiple_approve_and_proviso(self):
        other_user = GovUserFactory(team=self.team)

        # given there is a case
        case = self.create_standard_application_case(self.organisation)
        good = self.create_good("A good", self.organisation)

        # and the case has an approve
        factories.UserAdviceFactory.create(type=AdviceType.APPROVE, case=case, user=self.gov_user, good=good)
        # and a proviso
        factories.UserAdviceFactory.create(type=AdviceType.PROVISO, case=case, user=other_user, good=good)

        # when the advice is collated
        advice.group_advice(
            case=case, advice=case.advice.all(), user=self.base_user, new_level="team",
        )

        # then there is no conflict
        case.refresh_from_db()
        self.assertEqual(case.advice.all().count(), 3)
        self.assertEqual(case.advice.all().get(level="team").type, AdviceType.PROVISO)

    def test_group_advice_multiple_approve_and_reject(self):
        other_user = GovUserFactory(team=self.team)

        # given there is a case
        case = self.create_standard_application_case(self.organisation)
        good = self.create_good("A good", self.organisation)
        # and the case has an approve
        factories.UserAdviceFactory.create(type=AdviceType.APPROVE, case=case, user=self.gov_user, good=good)
        # and the case has an reject
        factories.UserAdviceFactory.create(type=AdviceType.REFUSE, case=case, user=other_user, good=good)

        # when the advice is collated
        advice.group_advice(
            case=case, advice=case.advice.all(), user=self.base_user, new_level="team",
        )

        # then there is a conflict
        case.refresh_from_db()
        self.assertEqual(case.advice.all().count(), 3)
        self.assertEqual(case.advice.all().get(level="team").type, AdviceType.CONFLICTING)

    def test_users_from_two_teams_can_give_advice(self):
        other_team = TeamFactory()
        other_user = GovUserFactory(team=self.team)
        other_teams_user = GovUserFactory(team=other_team)

        # given there is a case
        case = self.create_standard_application_case(self.organisation)
        good = self.create_good("A good", self.organisation)

        # and the case has collated advice from one team
        factories.UserAdviceFactory.create(type=AdviceType.APPROVE, case=case, user=self.gov_user, good=good)
        factories.UserAdviceFactory.create(type=AdviceType.REFUSE, case=case, user=other_user, good=good)
        advice.group_advice(
            case=case, advice=case.advice.all(), user=self.gov_user.baseuser_ptr, new_level="team",
        )

        # another user from a different team can still give advice
        factories.UserAdviceFactory.create(type=AdviceType.APPROVE, case=case, user=other_teams_user, good=good)

        case.refresh_from_db()
        self.assertEqual(case.advice.all().filter(level="user").count(), 3)
        self.assertEqual(case.advice.all().filter(level="team").count(), 1)

        # user from another team can also combine their team's advice
        advice.group_advice(
            case=case, advice=case.advice.all(), user=other_teams_user.baseuser_ptr, new_level="team",
        )

        case.refresh_from_db()
        self.assertEqual(case.advice.all().filter(level="user").count(), 3)
        self.assertEqual(case.advice.all().filter(level="team").count(), 2)
