import unittest

from django.urls import reverse_lazy
from parameterized import parameterized
from rest_framework import status

from api.applications.models import GoodOnApplication, PartyOnApplication, CountryOnApplication
from api.applications.tests.factories import PartyOnApplicationFactory
from api.cases.enums import CaseTypeEnum
from api.core import constants
from api.flags.enums import FlagLevels, FlagStatuses
from api.flags.models import Flag, FlaggingRule
from api.goods.enums import GoodStatus
from api.goods.tests.factories import GoodFactory
from api.goodstype.models import GoodsType
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.control_list_entries.helpers import (
    get_clc_child_nodes,
    get_clc_parent_nodes,
    get_control_list_entry,
)
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.teams.models import Team
from test_helpers.clients import DataTestClient
from api.workflow.flagging_rules_automation import (
    apply_flagging_rules_to_case,
    apply_case_flagging_rules,
    apply_goods_rules_for_good,
    apply_destination_rule_on_party,
    get_active_legacy_flagging_rules_for_level,
    apply_flagging_rule_to_all_open_cases,
)
from api.users.models import Role


class FlaggingRulesAutomation(DataTestClient):
    def test_adding_case_type_flag(self):
        flag = self.create_flag(name="case flag", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.CASE, team=self.team, flag=flag, matching_values=[CaseTypeEnum.EXHIBITION.reference]
        )

        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(case)

        apply_flagging_rules_to_case(case)

        case.refresh_from_db()

        self.assertTrue(flag in list(case.flags.all()))

    def test_adding_goods_type_flag_from_case(self):
        flag = self.create_flag(name="good flag", level=FlagLevels.GOOD, team=self.team)
        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(case)
        good = GoodOnApplication.objects.filter(application_id=case.id).first().good
        self.create_flagging_rule(
            level=FlagLevels.GOOD, team=self.team, flag=flag, matching_values=[good.control_list_entries.first().rating]
        )

        apply_flagging_rules_to_case(case)

        good_flags = list(good.flags.all())

        self.assertTrue(flag in good_flags)

    def test_adding_goods_type_flag_with_exclusion_entries(self):
        flag = self.create_flag(name="good flag", level=FlagLevels.GOOD, team=self.team)
        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(case)
        good = GoodOnApplication.objects.filter(application_id=case.id).first().good
        self.create_flagging_rule(
            level=FlagLevels.GOOD,
            team=self.team,
            flag=flag,
            matching_values=[good.control_list_entries.first().rating],
            matching_groups=["ML5"],
            excluded_values=[good.control_list_entries.first().rating],
        )

        apply_flagging_rules_to_case(case)

        good.flags.count() >= 1

    def test_goods_flag_before_and_after_reviewing_good(self):
        """Tests applying of flagging rule with a matching group and excluding entry.
        Reviews the good and updates the entry to match with excluding entry and ensures that
        the flag is now cleared after review.
        """
        flag = self.create_flag(name="good flag", level=FlagLevels.GOOD, team=self.team)
        case = self.create_draft_standard_application(self.organisation)
        self.submit_application(case)
        good = GoodOnApplication.objects.filter(application_id=case.id).first().good

        good.control_list_entries.set(ControlListEntry.objects.filter(rating="ML8a"))
        good.save()
        self.create_flagging_rule(
            level=FlagLevels.GOOD,
            team=self.team,
            flag=flag,
            matching_values=[],
            matching_groups=["ML8"],
            excluded_values=["ML8b"],
        )

        apply_flagging_rules_to_case(case)
        assert good.flags.count() >= 3

        role = Role(name="review_goods")
        role.permissions.set([constants.GovPermissions.REVIEW_GOODS.name])
        role.save()
        self.gov_user.role = role
        self.gov_user.save()

        self.url = reverse_lazy("goods:control_list_entries", kwargs={"case_pk": case.id})
        data = {
            "objects": [good.id],
            "current_object": good.id,
            "comment": "Update rating to match with flag excluded value",
            "report_summary": "test report summary",
            "control_list_entries": ["ML8b"],
            "is_good_controlled": True,
            "regime_entries": [],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert good.flags.count() >= 3

    def test_adding_goods_type_flag_from_case_with_verified_only_rule_failure(self):
        """Test flag not applied to good when flagging rule is for verified goods only."""
        flag = self.create_flag(name="for verified good flag", level=FlagLevels.GOOD, team=self.team)
        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(case)
        good = GoodOnApplication.objects.filter(application_id=case.id).first().good

        self.create_flagging_rule(
            level=FlagLevels.GOOD,
            team=self.team,
            flag=flag,
            matching_values=[good.control_list_entries.first().rating],
            is_for_verified_goods_only=True,
        )

        apply_flagging_rules_to_case(case)

        good_flags = list(good.flags.all())
        self.assertFalse(flag in good_flags)

    def test_adding_goods_type_flag_from_case_with_verified_only_rule_success(self):
        """Test flag is applied to verified good when the flagging rule is applicable to only verified goods."""
        flag = self.create_flag(name="for verified good flag", level=FlagLevels.GOOD, team=self.team)
        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(case)
        good = GoodOnApplication.objects.filter(application_id=case.id).first().good
        good.status = GoodStatus.VERIFIED
        good.save()

        self.create_flagging_rule(
            level=FlagLevels.GOOD,
            team=self.team,
            flag=flag,
            matching_values=[good.control_list_entries.first().rating],
            is_for_verified_goods_only=True,
        )

        apply_flagging_rules_to_case(case)

        good_flags = list(good.flags.all())
        self.assertTrue(flag in good_flags)

    def test_adding_destination_type_flag_from_case(self):
        flag = self.create_flag(name="good flag", level=FlagLevels.DESTINATION, team=self.team)
        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        self.submit_application(case)
        party = PartyOnApplication.objects.filter(application_id=case.id).first().party
        self.create_flagging_rule(
            level=FlagLevels.DESTINATION, team=self.team, flag=flag, matching_values=[party.country_id]
        )

        apply_flagging_rules_to_case(case)

        party_flags = list(party.flags.all())

        self.assertTrue(flag in party_flags)

    def test_case_dont_add_deactivated_flag(self):
        flag = self.create_flag(name="case flag", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.CASE, team=self.team, flag=flag, matching_values=[CaseTypeEnum.EXHIBITION.reference]
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
            matching_values=[CaseTypeEnum.EXHIBITION.reference],
            status=FlagStatuses.DEACTIVATED,
        )

        case = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)

        apply_flagging_rules_to_case(case)

        case.refresh_from_db()

        self.assertTrue(flag not in list(case.flags.all()))

    def test_get_active_flagging_rules_goods(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.GOOD, team=self.team)
        self.create_flagging_rule(level=FlagLevels.GOOD, team=self.team, flag=active_flag, matching_values=["abc"])

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.GOOD, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.GOOD,
            team=self.team,
            flag=deactivated_flag,
            matching_values=["abc"],
            status=FlagStatuses.DEACTIVATED,
        )

        flagging_rules = list(get_active_legacy_flagging_rules_for_level(level=FlagLevels.GOOD))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flag_flagging_rules_goods(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.GOOD, team=self.team)
        self.create_flagging_rule(level=FlagLevels.GOOD, team=self.team, flag=active_flag, matching_values=["abc"])

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.GOOD, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.GOOD,
            team=self.team,
            flag=deactivated_flag,
            matching_values=["abc"],
        )
        deactivated_flag.status = FlagStatuses.DEACTIVATED
        deactivated_flag.save()

        flagging_rules = list(get_active_legacy_flagging_rules_for_level(level=FlagLevels.GOOD))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flagging_rules_destination(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.DESTINATION, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.DESTINATION, team=self.team, flag=active_flag, matching_values=["abc"]
        )

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.DESTINATION, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.DESTINATION,
            team=self.team,
            flag=deactivated_flag,
            matching_values=["abc"],
            status=FlagStatuses.DEACTIVATED,
        )

        flagging_rules = list(get_active_legacy_flagging_rules_for_level(level=FlagLevels.DESTINATION))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flag_flagging_rules_destination(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.DESTINATION, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.DESTINATION, team=self.team, flag=active_flag, matching_values=["abc"]
        )

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.DESTINATION, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.DESTINATION,
            team=self.team,
            flag=deactivated_flag,
            matching_values=["abc"],
        )
        deactivated_flag.status = FlagStatuses.DEACTIVATED
        deactivated_flag.save()

        flagging_rules = list(get_active_legacy_flagging_rules_for_level(level=FlagLevels.DESTINATION))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flagging_rules_case(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(level=FlagLevels.CASE, team=self.team, flag=active_flag, matching_values=["abc"])

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.CASE,
            team=self.team,
            flag=deactivated_flag,
            matching_values=["abc"],
            status=FlagStatuses.DEACTIVATED,
        )

        flagging_rules = list(get_active_legacy_flagging_rules_for_level(level=FlagLevels.CASE))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    def test_get_active_flag_flagging_rules_case(self):
        active_flag = self.create_flag(name="good flag", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(level=FlagLevels.CASE, team=self.team, flag=active_flag, matching_values=["abc"])

        deactivated_flag = self.create_flag(name="good flag 2", level=FlagLevels.CASE, team=self.team)
        self.create_flagging_rule(
            level=FlagLevels.CASE,
            team=self.team,
            flag=deactivated_flag,
            matching_values=["abc"],
        )
        deactivated_flag.status = FlagStatuses.DEACTIVATED
        deactivated_flag.save()

        flagging_rules = list(get_active_legacy_flagging_rules_for_level(level=FlagLevels.CASE))

        self.assertTrue(active_flag in [rule.flag for rule in flagging_rules])
        self.assertTrue(deactivated_flag not in [rule.flag for rule in flagging_rules])

    @parameterized.expand([k for k, v in CaseStatusEnum.choices])
    def test_apply_flagging_rule_to_open_cases(self, case_status):
        if case_status == CaseStatusEnum.DRAFT:
            case = self.create_draft_standard_application(self.organisation)
        else:
            case = self.create_standard_application_case(self.organisation)
            case.status = get_case_status_by_status(case_status)
            case.save()

        flag = self.create_flag(case.case_type.reference, FlagLevels.CASE, self.team)
        flagging_rule = self.create_flagging_rule(FlagLevels.CASE, self.team, flag, [case.case_type.reference])

        apply_flagging_rule_to_all_open_cases(flagging_rule)

        case.refresh_from_db()

        if CaseStatusEnum.is_terminal(case_status) or case_status == CaseStatusEnum.DRAFT:
            self.assertNotIn(flag, case.flags.all())
        else:
            self.assertIn(flag, case.flags.all())

    def test_apply_verified_goods_only_flagging_rule_to_open_cases_failure(self):
        """Test flag not applied to good when flagging rule is for verified goods only."""
        case = self.create_standard_application_case(self.organisation)

        flag = self.create_flag("good flag", FlagLevels.GOOD, self.team)
        flagging_rule = self.create_flagging_rule(
            FlagLevels.GOOD, self.team, flag, [case.case_type.reference], is_for_verified_goods_only=True
        )
        good = GoodOnApplication.objects.filter(application_id=case.id).first().good

        apply_flagging_rule_to_all_open_cases(flagging_rule)

        case.refresh_from_db()
        self.assertNotIn(flag, case.flags.all())

    def test_apply_verified_goods_only_flagging_rule_to_open_cases_success(self):
        case = self.create_standard_application_case(self.organisation)

        flag = self.create_flag("good flag", FlagLevels.GOOD, self.team)
        flagging_rule = self.create_flagging_rule(
            FlagLevels.GOOD, self.team, flag, [case.case_type.reference], is_for_verified_goods_only=True
        )
        good = GoodOnApplication.objects.filter(application_id=case.id).first().good
        good.status = GoodStatus.VERIFIED
        good.save()

        apply_flagging_rule_to_all_open_cases(flagging_rule)

        case.refresh_from_db()
        self.assertNotIn(flag, case.flags.all())

    @unittest.mock.patch("api.workflow.flagging_rules_automation.run_flagging_rules_criteria_case")
    def test_python_criteria_satisfied_calls_case_criteria_function(self, mocked_criteria_function):
        mocked_criteria_function.return_value = True
        rule = FlaggingRule.objects.create(
            team=Team.objects.first(),
            flag=Flag.objects.first(),
            level=FlagLevels.CASE,
            status=FlagStatuses.ACTIVE,
            is_python_criteria=True,
        )
        case = self.create_standard_application_case(self.organisation)
        case.flags.clear()
        self.assertEqual(case.flags.count(), 0)
        apply_case_flagging_rules(case)
        assert mocked_criteria_function.called
        self.assertIn(rule.flag, case.flags.all())

    @unittest.mock.patch("api.workflow.flagging_rules_automation.run_flagging_rules_criteria_product")
    def test_python_criteria_satisfied_calls_product_criteria_function(self, mocked_criteria_function):
        mocked_criteria_function.return_value = True
        rule = FlaggingRule.objects.create(
            team=Team.objects.first(),
            flag=Flag.objects.first(),
            level=FlagLevels.GOOD,
            status=FlagStatuses.ACTIVE,
            is_python_criteria=True,
        )
        good = GoodFactory(organisation=self.organisation)
        self.assertEqual(good.flags.count(), 0)
        apply_goods_rules_for_good(good)
        assert mocked_criteria_function.called
        self.assertIn(rule.flag, good.flags.all())

    @unittest.mock.patch("api.workflow.flagging_rules_automation.run_flagging_rules_criteria_destination")
    def test_python_criteria_satisfied_calls_destination_criteria_function(self, mocked_criteria_function):
        mocked_criteria_function.return_value = True
        rule = FlaggingRule.objects.create(
            team=Team.objects.first(),
            flag=Flag.objects.first(),
            level=FlagLevels.DESTINATION,
            status=FlagStatuses.ACTIVE,
            is_python_criteria=True,
        )
        party_on_application = PartyOnApplicationFactory(party__country__id="US")
        party = party_on_application.party
        self.assertEqual(party.flags.count(), 0)
        apply_destination_rule_on_party(party)
        assert mocked_criteria_function.called
        self.assertIn(rule.flag, party.flags.all())


class FlaggingRulesAutomationForEachCaseType(DataTestClient):
    def test_open_application_automation(self):
        application = self.create_draft_open_application(self.organisation)

        case_flag = self.create_flag("case flag", FlagLevels.CASE, self.team)
        self.create_flagging_rule(
            FlagLevels.CASE, self.team, flag=case_flag, matching_values=[application.case_type.reference]
        )

        goods_type = GoodsType.objects.filter(application_id=application.id).first()
        good_flag = self.create_flag("good flag", FlagLevels.GOOD, self.team)
        self.create_flagging_rule(
            FlagLevels.GOOD,
            self.team,
            flag=good_flag,
            matching_values=[goods_type.control_list_entries.first().rating],
            is_for_verified_goods_only=False,
        )

        country = CountryOnApplication.objects.filter(application_id=application.id).first().country
        destination_flag = self.create_flag("dest flag", FlagLevels.DESTINATION, self.team)
        dest_flagging_rule = self.create_flagging_rule(
            FlagLevels.DESTINATION, self.team, flag=destination_flag, matching_values=[country.id]
        )
        apply_flagging_rule_to_all_open_cases(dest_flagging_rule)

        self.submit_application(application)
        apply_flagging_rules_to_case(application)

        application.refresh_from_db()
        goods_type.refresh_from_db()
        country.refresh_from_db()

        self.assertIn(case_flag, application.flags.all())
        self.assertIn(good_flag, goods_type.flags.all())
        self.assertIn(destination_flag, country.flags.all())

    def test_standard_application(self):
        application = self.create_standard_application_case(self.organisation)

        case_flag = self.create_flag("case flag", FlagLevels.CASE, self.team)
        self.create_flagging_rule(
            FlagLevels.CASE, self.team, flag=case_flag, matching_values=[application.case_type.reference]
        )

        good = GoodOnApplication.objects.filter(application_id=application.id).first().good
        good_flag = self.create_flag("good flag", FlagLevels.GOOD, self.team)
        self.create_flagging_rule(
            FlagLevels.GOOD, self.team, flag=good_flag, matching_values=[good.control_list_entries.first().rating]
        )

        party = PartyOnApplication.objects.filter(application_id=application.id).first().party
        destination_flag = self.create_flag("dest flag", FlagLevels.DESTINATION, self.team)
        self.create_flagging_rule(
            FlagLevels.DESTINATION, self.team, flag=destination_flag, matching_values=[party.country_id]
        )

        self.submit_application(application)
        apply_flagging_rules_to_case(application)

        application.refresh_from_db()
        good.refresh_from_db()
        party.refresh_from_db()

        self.assertIn(case_flag, application.flags.all())
        self.assertIn(good_flag, good.flags.all())
        self.assertIn(destination_flag, party.flags.all())

    def test_hmrc_application(self):
        application = self.create_hmrc_query(self.organisation)

        case_flag = self.create_flag("case flag", FlagLevels.CASE, self.team)
        self.create_flagging_rule(
            FlagLevels.CASE, self.team, flag=case_flag, matching_values=[application.case_type.reference]
        )

        goods_type = GoodsType.objects.filter(application_id=application.id).first()
        good_flag = self.create_flag("good flag", FlagLevels.GOOD, self.team)

        goods_type.control_list_entries.set([get_control_list_entry("ML1a")])
        self.create_flagging_rule(
            FlagLevels.GOOD, self.team, flag=good_flag, matching_values=[goods_type.control_list_entries.first().rating]
        )

        party = PartyOnApplication.objects.filter(application_id=application.id).first().party
        destination_flag = self.create_flag("dest flag", FlagLevels.DESTINATION, self.team)
        self.create_flagging_rule(
            FlagLevels.DESTINATION, self.team, flag=destination_flag, matching_values=[party.country_id]
        )

        self.submit_application(application)
        apply_flagging_rules_to_case(application)

        application.refresh_from_db()
        goods_type.refresh_from_db()
        party.refresh_from_db()

        self.assertIn(case_flag, application.flags.all())
        self.assertIn(good_flag, goods_type.flags.all())
        self.assertIn(destination_flag, party.flags.all())

    def test_F680_application(self):
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)

        case_flag = self.create_flag("case flag", FlagLevels.CASE, self.team)
        self.create_flagging_rule(
            FlagLevels.CASE, self.team, flag=case_flag, matching_values=[application.case_type.reference]
        )

        good = GoodOnApplication.objects.filter(application_id=application.id).first().good
        good_flag = self.create_flag("good flag", FlagLevels.GOOD, self.team)
        self.create_flagging_rule(
            FlagLevels.GOOD, self.team, flag=good_flag, matching_values=[good.control_list_entries.first().rating]
        )

        party = PartyOnApplication.objects.filter(application_id=application.id).first().party
        destination_flag = self.create_flag("dest flag", FlagLevels.DESTINATION, self.team)
        self.create_flagging_rule(
            FlagLevels.DESTINATION, self.team, flag=destination_flag, matching_values=[party.country_id]
        )

        self.submit_application(application)
        apply_flagging_rules_to_case(application)

        application.refresh_from_db()
        good.refresh_from_db()
        party.refresh_from_db()

        self.assertIn(case_flag, application.flags.all())
        self.assertIn(good_flag, good.flags.all())
        self.assertIn(destination_flag, party.flags.all())

    def test_exhibition_application(self):
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(application)

        case_flag = self.create_flag("case flag", FlagLevels.CASE, self.team)
        self.create_flagging_rule(
            FlagLevels.CASE, self.team, flag=case_flag, matching_values=[application.case_type.reference]
        )

        good = GoodOnApplication.objects.filter(application_id=application.id).first().good
        good_flag = self.create_flag("good flag", FlagLevels.GOOD, self.team)
        self.create_flagging_rule(
            FlagLevels.GOOD, self.team, flag=good_flag, matching_values=[good.control_list_entries.first().rating]
        )

        self.submit_application(application)
        apply_flagging_rules_to_case(application)

        application.refresh_from_db()
        good.refresh_from_db()

        self.assertIn(case_flag, application.flags.all())
        self.assertIn(good_flag, good.flags.all())

    def test_goods_query_application(self):
        query = self.create_clc_query("query", self.organisation)

        case_flag = self.create_flag("case flag", FlagLevels.CASE, self.team)
        self.create_flagging_rule(
            FlagLevels.CASE, self.team, flag=case_flag, matching_values=[query.case_type.reference]
        )

        good = query.good
        good.control_list_entries.set([get_control_list_entry("ML1a")])
        good_flag = self.create_flag("good flag", FlagLevels.GOOD, self.team)
        self.create_flagging_rule(
            FlagLevels.GOOD, self.team, flag=good_flag, matching_values=[good.control_list_entries.first().rating]
        )

        apply_flagging_rules_to_case(query)

        query.refresh_from_db()
        good.refresh_from_db()

        self.assertIn(case_flag, query.flags.all())
        self.assertIn(good_flag, good.flags.all())

    def test_end_user_advisory_application(self):
        query = self.create_end_user_advisory("a", "v", self.organisation)

        case_flag = self.create_flag("case flag", FlagLevels.CASE, self.team)
        self.create_flagging_rule(
            FlagLevels.CASE, self.team, flag=case_flag, matching_values=[query.case_type.reference]
        )

        party = query.end_user
        destination_flag = self.create_flag("dest flag", FlagLevels.DESTINATION, self.team)
        self.create_flagging_rule(
            FlagLevels.DESTINATION, self.team, flag=destination_flag, matching_values=[party.country_id]
        )

        apply_flagging_rules_to_case(query)

        query.refresh_from_db()
        party.refresh_from_db()

        self.assertIn(case_flag, query.flags.all())
        self.assertIn(destination_flag, party.flags.all())
