from django.test import tag

from applications.models import CountryOnApplication
from cases.models import CaseType
from static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from workflow.automation import run_routing_rules
from workflow.routing_rules.enum import RoutingRulesAdditionalFields


class ParameterSetRoutingRuleModelMethodTests(DataTestClient):
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

        parameter_sets = routing_rule.parameter_sets()
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

        parameter_sets = routing_rule.parameter_sets()

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

        parameter_sets = routing_rule.parameter_sets()

        self.assertEqual(len(parameter_sets), 1)


class ParameterSetCaseModelMethodTests(DataTestClient):
    @tag("2109")
    def test_case_parameters_are_returned_in_a_set(self):
        case = self.create_standard_application_case(organisation=self.organisation)

        case.flags.set([self.create_flag(name="1", team=self.team, level="case")])

        parameter_set = case.parameter_set()

        self.assertTrue(set(case.flags.all()).issubset(parameter_set))
        self.assertIn(case.case_type, parameter_set)

    @tag("2109")
    def test_parameter_Set_returned_for_open_application(self):
        case = self.create_open_application_case(organisation=self.organisation)

        parameter_set = case.parameter_set()

        self.assertTrue(
            set([coa.country for coa in CountryOnApplication.objects.filter(application=case.id)]).issubset(
                parameter_set
            )
        )
        self.assertIn(case.case_type, parameter_set)

    @tag("2109")
    def test_end_user_advisory_query_returns_parameter_set(self):
        case = self.create_end_user_advisory_case(organisation=self.organisation, note="a note", reasoning="reasoning")

        parameter_set = case.parameter_set()

        self.assertIn(case.case_type, parameter_set)

    @tag("2109")
    def test_good_query_returns_parameter_set(self):
        case = self.create_goods_query(
            organisation=self.organisation, clc_reason="reason", pv_reason="reason", description="a good"
        )

        parameter_set = case.parameter_set()

        self.assertIn(case.case_type, parameter_set)


class CaseRoutingAutomationTests(DataTestClient):
    @tag("2109")
    def test_case_routed_to_new_queue_when_status_changed(self):
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )

        case = self.create_open_application_case(organisation=self.organisation)
        run_routing_rules(case)

        self.assertIn(self.queue, case.queues.all())
