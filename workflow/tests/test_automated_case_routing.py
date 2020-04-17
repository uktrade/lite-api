from django.test import tag

from cases.models import CaseType
from flags.models import Flag
from static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from workflow.routing_rules.enum import RoutingRulesAdditionalFields


class CaseRoutingAutomationTests(DataTestClient):
    def test_case_routed_to_new_queue_when_status_changed(self):
        pass


class ParameterSetModelMethodTests(DataTestClient):
    def test_case_parameters_are_returned_in_a_set(self):
        pass

    @tag("2109")
    def test_routing_rule_parameters_are_returned_in_a_set(self):
        routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[*[k for k, v in RoutingRulesAdditionalFields.choices]],
        )

        parameter_sets = routing_rule.parameter_set()
        parameter_set = parameter_sets[0]

        self.assertTrue(set(routing_rule.flags.all()).issubset(parameter_set))

    @tag("2109")
    def test_routing_rule_parameters_returned_in_multiple_sets_for_multiple_case_types(self):
        routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[*[k for k, v in RoutingRulesAdditionalFields.choices]],
        )
        routing_rule.case_types.set(CaseType.objects.all())

        parameter_sets = routing_rule.parameter_set()

        self.assertEqual(len(parameter_sets), CaseType.objects.count())

    @tag("2109")
    def test_parameters_returned_if_no_case_types_set(self):
        routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[*[k for k, v in RoutingRulesAdditionalFields.choices]],
        )
        routing_rule.case_types.clear()

        parameter_sets = routing_rule.parameter_set()

        self.assertEqual(len(parameter_sets), 1)
