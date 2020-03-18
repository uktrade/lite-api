from applications.models import GoodOnApplication, PartyOnApplication
from cases.enums import CaseTypeEnum
from flags.enums import FlagLevels, FlagStatuses
from test_helpers.clients import DataTestClient
from workflow.flagging_rules_automation import apply_flagging_rules_to_case, active_flagging_rules_for_level


class FlaggingRulesAutomation(DataTestClient):
    def test_adding_case_type_flag(self):
        flag = self.create_flag(name="case flag", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.CASE, team=self.team, flag=flag, matching_value=CaseTypeEnum.EXHIBITION.reference
        )

        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)

        apply_flagging_rules_to_case(case)

        case.refresh_from_db()

        self.assertTrue(flag in list(case.flags.all()))

    def test_adding_goods_type_flag_from_case(self):
        flag = self.create_flag(name="good flag", level=FlagLevels.GOOD, team=self.team)
        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        good = GoodOnApplication.objects.filter(application_id=case.id).first().good
        self.create_flagging_rule(level=FlagLevels.GOOD, team=self.team, flag=flag, matching_value=good.control_code)

        apply_flagging_rules_to_case(case)

        good_flags = list(good.flags.all())

        self.assertTrue(flag in good_flags)

    def test_adding_destination_type_flag_from_case(self):
        flag = self.create_flag(name="good flag", level=FlagLevels.DESTINATION, team=self.team)
        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        party = PartyOnApplication.objects.filter(application_id=case.id).first().party
        self.create_flagging_rule(
            level=FlagLevels.DESTINATION, team=self.team, flag=flag, matching_value=party.country_id
        )

        apply_flagging_rules_to_case(case)

        party_flags = list(party.flags.all())

        self.assertTrue(flag in party_flags)

    def test_case_dont_add_deactivated_flag(self):
        flag = self.create_flag(name="case flag", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.CASE, team=self.team, flag=flag, matching_value=CaseTypeEnum.EXHIBITION.reference
        )
        flag.status = FlagStatuses.DEACTIVATED
        flag.save()

        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)

        apply_flagging_rules_to_case(case)

        case.refresh_from_db()

        self.assertTrue(flag not in list(case.flags.all()))

    def test_case_dont_add_deactivated_flagging_rule(self):
        flag = self.create_flag(name="case flag", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.CASE,
            team=self.team,
            flag=flag,
            matching_value=CaseTypeEnum.EXHIBITION.reference,
            status=FlagStatuses.DEACTIVATED,
        )

        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)

        apply_flagging_rules_to_case(case)

        case.refresh_from_db()

        self.assertTrue(flag not in list(case.flags.all()))

    def test_get_active_flagging_rules_goods(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.GOOD, team=self.team)
        self.create_flagging_rule(level=FlagLevels.GOOD, team=self.team, flag=active_flag, matching_value="abc")

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.GOOD, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.GOOD,
            team=self.team,
            flag=deactivated_flag,
            matching_value="abc",
            status=FlagStatuses.DEACTIVATED,
        )

        flagging_rules = list(active_flagging_rules_for_level(level=FlagLevels.GOOD))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flag_flagging_rules_goods(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.GOOD, team=self.team)
        self.create_flagging_rule(level=FlagLevels.GOOD, team=self.team, flag=active_flag, matching_value="abc")

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.GOOD, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.GOOD, team=self.team, flag=deactivated_flag, matching_value="abc",
        )
        deactivated_flag.status = FlagStatuses.DEACTIVATED
        deactivated_flag.save()

        flagging_rules = list(active_flagging_rules_for_level(level=FlagLevels.GOOD))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flagging_rules_destination(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.DESTINATION, team=self.team)
        self.create_flagging_rule(level=FlagLevels.DESTINATION, team=self.team, flag=active_flag, matching_value="abc")

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.DESTINATION, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.DESTINATION,
            team=self.team,
            flag=deactivated_flag,
            matching_value="abc",
            status=FlagStatuses.DEACTIVATED,
        )

        flagging_rules = list(active_flagging_rules_for_level(level=FlagLevels.DESTINATION))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flag_flagging_rules_destination(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.DESTINATION, team=self.team)
        self.create_flagging_rule(level=FlagLevels.DESTINATION, team=self.team, flag=active_flag, matching_value="abc")

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.DESTINATION, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.DESTINATION, team=self.team, flag=deactivated_flag, matching_value="abc",
        )
        deactivated_flag.status = FlagStatuses.DEACTIVATED
        deactivated_flag.save()

        flagging_rules = list(active_flagging_rules_for_level(level=FlagLevels.DESTINATION))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flagging_rules_case(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(level=FlagLevels.CASE, team=self.team, flag=active_flag, matching_value="abc")

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.CASE,
            team=self.team,
            flag=deactivated_flag,
            matching_value="abc",
            status=FlagStatuses.DEACTIVATED,
        )

        flagging_rules = list(active_flagging_rules_for_level(level=FlagLevels.CASE))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flag_flagging_rules_case(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(level=FlagLevels.CASE, team=self.team, flag=active_flag, matching_value="abc")

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.CASE, team=self.team, flag=deactivated_flag, matching_value="abc",
        )
        deactivated_flag.status = FlagStatuses.DEACTIVATED
        deactivated_flag.save()

        flagging_rules = list(active_flagging_rules_for_level(level=FlagLevels.CASE))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])
