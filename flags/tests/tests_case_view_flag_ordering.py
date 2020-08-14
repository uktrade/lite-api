from api.applications.models import GoodOnApplication, PartyOnApplication
from cases.libraries.get_flags import get_ordered_flags
from flags.enums import FlagLevels
from flags.tests.factories import FlagFactory
from api.parties.enums import PartyType
from teams.tests.factories import TeamFactory
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

        ordered_flags = get_ordered_flags(case, self.team)

        # This is the order of the original flags when displayed on a case
        expected_order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 16, 9, 17, 10, 18, 11, 19, 12, 20, 13, 21, 14, 22, 15, 23]

        for i in range(0, 24):
            if i <= 7:
                self.assertIn(flags[expected_order[i]].name, str(ordered_flags[i]))
            else:
                # We don't know about the order here by team, it doesn't matter as long as its by priority and type correctly
                if i % 2 == 0:
                    self.assertIn(flags[expected_order[i]].name, str(ordered_flags[i]) + str(ordered_flags[i + 1]))
                else:
                    self.assertIn(flags[expected_order[i]].name, str(ordered_flags[i]) + str(ordered_flags[i - 1]))
            i += 1
