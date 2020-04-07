from django.test import tag

from applications.models import GoodOnApplication, PartyOnApplication
from cases.libraries.get_destination import get_ordered_flags
from flags.tests.factories import FlagFactory
from parties.enums import PartyType
from teams.models import Team
from test_helpers.clients import DataTestClient


class FlagsOrderingOnCaseViewTests(DataTestClient):
    @tag("only")
    def test_gov_user_can_see_all_flags(self):
        # create 16 flags, 2 of each level for two different teams with different priorities
        other_team = Team(name="Other")
        other_team.save()
        third_team = Team(name="Third")
        third_team.save()

        flags = []

        for team in [self.team, other_team, third_team]:
            for level in ["Case", "Good", "Destination", "Organisation"]:
                for priority in [0, 1]:
                    flag = FlagFactory(
                        name=level + team.name + str(priority), level=level, priority=priority, team=team
                    )
                    flags.append(flag)

        print(flags)
        print("\n")
        case = self.create_standard_application_case(organisation=self.organisation)
        case.flags.set([flag for flag in flags if flag.level == "Case"])
        print(case.flags.values_list("name"))
        print("\n")

        good = GoodOnApplication.objects.get(application=case).good
        good.flags.set([flag for flag in flags if flag.level == "Good"])
        print(good.flags.values_list("name"))
        print("\n")

        end_user = PartyOnApplication.objects.get(application=case, party__type=PartyType.END_USER).party
        end_user.flags.set([flag for flag in flags if flag.level == "Destination"])
        print(end_user.flags.values_list("name"))
        print("\n")

        self.organisation.flags.set([flag for flag in flags if flag.level == "Organisation"])
        print(self.organisation.flags.values_list("name"))
        print("\n")

        ordered_flags = get_ordered_flags(case, self.team)

        for flag in ordered_flags:
            print(flag)
