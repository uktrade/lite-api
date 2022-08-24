import unittest

from api.workflow.routing_rules.models import RoutingRule
from api.teams.models import Team
from api.queues.models import Queue
from api.cases.models import CaseStatus
from test_helpers.clients import DataTestClient


class RoutingRuleCreationTests(DataTestClient):
    def test_is_python_criteria_satisfied_non_python_rule(self):
        rule = RoutingRule.objects.create(
            team=Team.objects.first(),
            queue=Queue.objects.first(),
            status=CaseStatus.objects.first(),
            tier=2,
        )
        self.assertRaises(NotImplementedError, rule.is_python_criteria_satisfied, unittest.mock.Mock())

    @unittest.mock.patch("api.workflow.routing_rules.models.run_criteria_function")
    def test_is_python_criteria_satisfied_calls_criteria_function(self, mocked_run_criteria_function):
        mocked_run_criteria_function.return_value = True
        rule = RoutingRule.objects.create(
            team=Team.objects.first(),
            queue=Queue.objects.first(),
            status=CaseStatus.objects.first(),
            tier=2,
            is_python_criteria=True,
        )
        assert rule.is_python_criteria_satisfied(unittest.mock.Mock()) == True
        assert mocked_run_criteria_function.called
