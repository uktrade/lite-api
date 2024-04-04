from api.flags.enums import FlagLevels


class FlaggingRulesRouter:
    def __init__(self):
        self._rules = {
            FlagLevels.CASE: [],
            FlagLevels.GOOD: [],
            FlagLevels.DESTINATION: [],
        }

    def register(self, *, level, flag_id):
        def _register(fn):
            self._rules[level].append((fn, flag_id))
            return fn

        return _register

    def get_rules(self, level):
        return self._rules[level]


flagging_rules = FlaggingRulesRouter()


class RoutingRulesRouter:
    def __init__(self):
        self._rules = {}

    def register(self, *, rule_pk):
        def _register(fn):
            self._rules[str(rule_pk)] = fn
            return fn

        return _register

    def get_criteria_function(self, rule_pk):
        try:
            return self._rules[str(rule_pk)]
        except KeyError:
            raise NotImplementedError(f"criteria_function for rule {rule_pk} does not exist")

    def has_criteria_function(self, rule_pk):
        return str(rule_pk) in self._rules


routing_rules = RoutingRulesRouter()
