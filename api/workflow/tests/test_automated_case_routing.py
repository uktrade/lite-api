from api.applications.models import PartyOnApplication
from api.cases.models import CaseType
from api.flags.enums import FlagStatuses
from api.flags.tests.factories import FlagFactory
from api.parties.models import Party
from api.staticdata.countries.models import Country
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from api.workflow.routing_rules.enum import RoutingRulesAdditionalFields


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

    def test_end_user_advisory_query_returns_parameter_set(self):
        case = self.create_end_user_advisory_case(organisation=self.organisation, note="a note", reasoning="reasoning")

        parameter_set = case.parameter_set()

        self.assertIn(case.case_type, parameter_set)

    def test_good_query_returns_parameter_set(self):
        case = self.create_goods_query(
            organisation=self.organisation, clc_reason="reason", pv_reason="reason", description="a good"
        )

        parameter_set = case.parameter_set()

        self.assertIn(case.case_type, parameter_set)
