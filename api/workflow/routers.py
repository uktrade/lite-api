from collections import defaultdict
from operator import itemgetter

from api.cases.enums import CaseTypeSubTypeEnum
from api.flags.enums import FlagLevels


class FlaggingRulesRouter:
    def __init__(self):
        self._rules = {
            case_sub_type: {
                FlagLevels.CASE: [],
                FlagLevels.GOOD: [],
                FlagLevels.DESTINATION: [],
            }
            for case_sub_type, _ in CaseTypeSubTypeEnum.choices
        }

    def register(self, *, case_sub_type, level, flag_id):
        def _register(fn):
            self._rules[case_sub_type][level].append((fn, flag_id))
            return fn

        return _register

    def get_rules(self, case_sub_type, level):
        return self._rules[case_sub_type][level]


flagging_rules = FlaggingRulesRouter()


class RoutingRulesRouter:
    def __init__(self):
        self._rules = {
            case_sub_type: defaultdict(lambda: defaultdict(list)) for case_sub_type, _ in CaseTypeSubTypeEnum.choices
        }

    def register(self, *, rule_id, case_sub_type, case_status, team, tier, queue, active=True):
        def _register(fn):
            self._rules[str(case_sub_type)][str(case_status)][str(team)].append(
                ((str(rule_id), tier, fn, str(queue)), active)
            )
            return fn

        return _register

    def _is_active(self, active):
        if callable(active):
            # Useful if we want to set a rule being active based on a callable.
            # This is required if we want to check settings that can be
            # dynamically overriden in tests.
            return active()
        return active

    def get_rules(self, case_sub_type, case_status, team):
        rules = self._rules[str(case_sub_type)][str(case_status)][str(team)]
        rules = [rule for rule, active in rules if self._is_active(active)]
        rules = sorted(rules, key=itemgetter(1))
        return rules


routing_rules = RoutingRulesRouter()
