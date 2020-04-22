from django.test import tag

from applications.models import CountryOnApplication, PartyOnApplication
from cases.models import CaseType
from flags.tests.factories import FlagFactory
from parties.models import Party
from queues.models import Queue
from static.countries.models import Country
from static.statuses.models import CaseStatus
from teams.models import Team
from test_helpers.clients import DataTestClient
from workflow.automation import run_routing_rules
from workflow.routing_rules.enum import RoutingRulesAdditionalFields


class ParameterSetRoutingRuleModelMethodTests(DataTestClient):
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
    @tag("2109", "only")
    def test_case_parameters_are_returned_in_a_set(self):
        case = self.create_standard_application_case(organisation=self.organisation)

        case.flags.set([self.create_flag(name="1", team=self.team, level="case")])

        party = Party(country=Country.objects.get(id="FR"), name="name", address="address")
        party.save()
        flag_2 = self.create_flag(name="2", team=self.team, level="destination")
        Country.objects.get(id="FR").flags.add(flag_2)
        PartyOnApplication(application=case, party=party).save()

        parameter_set = case.parameter_set()

        self.assertTrue(set(case.flags.all()).issubset(parameter_set))
        self.assertIn(case.case_type, parameter_set)
        self.assertIn(flag_2, parameter_set)
        self.assertIn(Country.objects.get(id="FR"), parameter_set)

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

    @tag("2109")
    def test_case_routed_to_multiple_queues_when_status_changed(self):
        queue_2 = Queue(team=self.team)
        queue_2.save()
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=queue_2.id,
            tier=5,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )

        case = self.create_open_application_case(organisation=self.organisation)
        run_routing_rules(case)

        self.assertIn(self.queue, set(case.queues.all()))
        self.assertIn(queue_2, set(case.queues.all()))

    @tag("2109")
    def test_case_routed_to_one_queue_with_different_rule_tiers_same_team_when_status_changed(self):
        queue_2 = Queue(team=self.team)
        queue_2.save()
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=queue_2.id,
            tier=6,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )

        case = self.create_open_application_case(organisation=self.organisation)
        run_routing_rules(case)

        self.assertIn(self.queue, case.queues.all())
        self.assertNotIn(queue_2, case.queues.all())

    @tag("2109")
    def test_case_routed_to_multiple_queues_with_multiple_team_rules_status_changed(self):
        queue_2 = Queue(team=self.team)
        queue_2.save()
        team_2 = Team(name="team2")
        team_2.save()
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )
        self.create_routing_rule(
            team_id=team_2.id,
            queue_id=queue_2.id,
            tier=6,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )

        case = self.create_open_application_case(organisation=self.organisation)
        run_routing_rules(case)

        self.assertIn(self.queue, set(case.queues.all()))
        self.assertIn(queue_2, set(case.queues.all()))

    @tag("2109")
    def test_case_routed_to_one_queue_with_multiple_team_rules_status_changed(self):
        team_2 = Team(name="team2")
        team_2.save()
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )
        self.create_routing_rule(
            team_id=team_2.id,
            queue_id=self.queue.id,
            tier=6,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )

        case = self.create_open_application_case(organisation=self.organisation)
        run_routing_rules(case)

        self.assertIn(self.queue, set(case.queues.all()))

    @tag("2109")
    def test_case_routed_to_multiple_queues_with_multiple_team_rules_at_different_tiers_status_changed(self):
        queue_2 = Queue(team=self.team)
        queue_2.save()
        queue_3 = Queue(team=self.team)
        queue_3.save()
        team_2 = Team(name="team2")
        team_2.save()
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )
        self.create_routing_rule(
            team_id=team_2.id,
            queue_id=queue_2.id,
            tier=5,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )
        self.create_routing_rule(
            team_id=team_2.id,
            queue_id=queue_3.id,
            tier=6,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )

        case = self.create_open_application_case(organisation=self.organisation)
        run_routing_rules(case)

        self.assertIn(self.queue, set(case.queues.all()))
        self.assertIn(queue_2, set(case.queues.all()))
        self.assertNotIn(queue_3, set(case.queues.all()))

    @tag("2109")
    def test_case_routed_by_second_tier_if_tier_one_conditions_not_met(self):
        queue_2 = Queue(team=self.team)
        queue_2.save()
        flag = FlagFactory(team=self.team)
        rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[RoutingRulesAdditionalFields.FLAGS],
        )
        rule.flags.add(flag)
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=queue_2.id,
            tier=6,
            status_id=CaseStatus.objects.get(status="submitted").id,
            additional_rules=[],
        )

        case = self.create_open_application_case(organisation=self.organisation)
        run_routing_rules(case)

        self.assertNotIn(self.queue, set(case.queues.all()))
        self.assertIn(queue_2, set(case.queues.all()))

    @tag("2109", "status")
    def test_case_advances_to_next_status_if_rules_not_run(self):
        queue_2 = Queue(team=self.team)
        queue_2.save()
        self.create_routing_rule(
            team_id=self.team.id,
            queue_id=queue_2.id,
            tier=6,
            status_id=CaseStatus.objects.get(status="under_review").id,
            additional_rules=[],
        )

        case = self.create_open_application_case(organisation=self.organisation)
        run_routing_rules(case)

        self.assertIn(queue_2, set(case.queues.all()))
