from itertools import chain

from api.applications.models import GoodOnApplication, PartyOnApplication
from api.cases.libraries.get_flags import get_ordered_flags
from api.flags.enums import FlagLevels
from api.flags.tests.factories import FlagFactory
from api.organisations.models import Organisation
from api.parties.enums import PartyType
from api.teams.tests.factories import TeamFactory
from test_helpers.clients import DataTestClient


class FlagsOrderingOnCaseViewTests(DataTestClient):
    def test_gov_user_can_see_all_flags(self):
        # create 16 flags, 2 of each level for two different teams with different priorities
        other_team = TeamFactory()
        third_team = TeamFactory()

        flags = []

        for team in [self.team, other_team, third_team]:
            for level in [FlagLevels.GOOD, FlagLevels.DESTINATION, FlagLevels.CASE, FlagLevels.ORGANISATION]:
                for priority in [0, 1]:
                    flag = FlagFactory(
                        name=level + team.name + str(priority), level=level, priority=priority, team=team
                    )
                    flags.append(flag)

        case = self.create_standard_application_case(organisation=self.organisation)
        case.flags.set([flag for flag in flags if flag.level == FlagLevels.CASE])

        good = GoodOnApplication.objects.get(application=case).good
        good.flags.set([flag for flag in flags if flag.level == FlagLevels.GOOD])

        end_user = PartyOnApplication.objects.get(application=case, party__type=PartyType.END_USER).party
        end_user.flags.set([flag for flag in flags if flag.level == FlagLevels.DESTINATION])

        self.organisation.flags.set([flag for flag in flags if flag.level == FlagLevels.ORGANISATION])

        actual_flags = sorted([item["name"] for item in get_ordered_flags(case, self.team)])
        expected_flags = sorted(
            [
                flag.name
                for flag in list(
                    chain(case.flags.all(), good.flags.all(), end_user.flags.all(), self.organisation.flags.all())
                )
            ]
            + ["Green Countries", "Green Countries"]
        )
        self.assertEqual(expected_flags, actual_flags)
