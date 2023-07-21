import unittest
import pytest

from api.applications.models import CountryOnApplication, PartyOnApplication
from api.cases.models import CaseType
from api.flags.enums import FlagStatuses
from api.flags.tests.factories import FlagFactory
from api.parties.models import Party
from api.staticdata.countries.models import Country
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from api.workflow.routing_rules.enum import RoutingRulesAdditionalFields


class ParameterSetRoutingRuleModelMethodTests(DataTestClient):
    def test_routing_rule_parameters_are_returned_in_a_set(self):
        routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[*[k for k, v in RoutingRulesAdditionalFields.choices]],
        )

        parameter_sets = routing_rule.parameter_sets()
        parameter_set = parameter_sets[0]["flags_country_set"]

        self.assertTrue(set(routing_rule.flags_to_include.all()).issubset(parameter_set))

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

    def test_inactive_flag_rule_returns_empty_list(self):
        flag = FlagFactory(status=FlagStatuses.DEACTIVATED, team=self.team)
        routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[*[k for k, v in RoutingRulesAdditionalFields.choices]],
        )
        routing_rule.flags_to_include.add(flag)

        parameter_sets = routing_rule.parameter_sets()

        self.assertEqual(len(parameter_sets), 0)


class ParameterSetCaseModelMethodTests(DataTestClient):
    def test_case_parameters_are_returned_in_a_set(self):
        case = self.create_standard_application_case(organisation=self.organisation)

        case.flags.set([self.create_flag(name="1", team=self.team, level="case")])
        france = Country.objects.get(id="FR")
        party = Party(country=france, name="name", address="address")
        party.save()
        flag_2 = self.create_flag(name="2", team=self.team, level="destination")
        france.flags.add(flag_2)
        PartyOnApplication(application=case, party=party).save()

        parameter_set = case.parameter_set()

        self.assertTrue(set(case.flags.all()).issubset(parameter_set))
        self.assertIn(case.case_type, parameter_set)
        self.assertIn(flag_2, parameter_set)
        self.assertIn(france, parameter_set)

    def test_parameter_set_returned_for_open_application(self):
        case = self.create_open_application_case(organisation=self.organisation)

        parameter_set = case.parameter_set()

        self.assertTrue(
            set([coa.country for coa in CountryOnApplication.objects.filter(application=case.id)]).issubset(
                parameter_set
            )
        )
        self.assertIn(case.case_type, parameter_set)

    def test_end_user_advisory_query_returns_parameter_set(self):
        case = self.create_end_user_advisory_case(organisation=self.organisation, note="a note", reasoning="reasoning")

        parameter_set = case.parameter_set()

        self.assertIn(case.case_type, parameter_set)
