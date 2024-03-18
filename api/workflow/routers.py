from enum import auto, Enum


class FlaggingRulesRouter:
    class Level(Enum):
        CASE = auto()
        PRODUCT = auto()
        DESTINATION = auto()

    def __init__(self):
        self._rules = {
            self.Level.CASE: {},
            self.Level.PRODUCT: {},
            self.Level.DESTINATION: {},
        }

    def register(self, *, level, rule_pk):
        def _register(fn):
            self._rules[level][rule_pk] = fn
            return fn

        return _register

    def get_criteria_function(self, level, rule_pk):
        try:
            return self._rules[level][str(rule_pk)]
        except KeyError:
            raise NotImplementedError(f"criteria_function for rule {rule_pk} does not exist")


flagging_rules = FlaggingRulesRouter()


class RoutingRulesRouter:
    def __init__(self):
        self._rules = {}

    def register(self, *, rule_pk):
        def _register(fn):
            self._rules[rule_pk] = fn
            return fn

        return _register

    def get_criteria_function(self, rule_pk):
        try:
            return self._rules[str(rule_pk)]
        except KeyError:
            raise NotImplementedError(f"criteria_function for rule {rule_pk} does not exist")


routing_rules = RoutingRulesRouter()
