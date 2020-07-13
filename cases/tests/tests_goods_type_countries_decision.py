from django.urls import reverse

from cases.enums import AdviceType
from cases.libraries.get_goods_type_countries_decisions import get_required_good_type_to_country_combinations
from cases.tests.factories import FinalAdviceFactory, GoodCountryDecisionFactory
from conf.constants import GovPermissions
from goodstype.tests.factories import GoodsTypeFactory
from static.control_list_entries.models import ControlListEntry
from static.countries.models import Country
from test_helpers.clients import DataTestClient


class FinaliseCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.case = self.create_open_application_case(self.organisation)
        self.url = reverse("cases:goods_countries_decisions", kwargs={"pk": self.case.id})
        # Covers every combination of APPROVE/REFUSE for goods_type on country
        self.countries = [Country.objects.first(), Country.objects.last()]
        self.approved_country = self.countries[0]
        self.refused_country = self.countries[1]
        self.approved_goods_type = GoodsTypeFactory(application=self.case)
        self.approved_goods_type.control_list_entries.set([ControlListEntry.objects.first()])
        self.approved_goods_type.countries.set(self.countries)
        self.refused_goods_type = GoodsTypeFactory(application=self.case)
        self.refused_goods_type.control_list_entries.set([ControlListEntry.objects.last()])
        self.refused_goods_type.countries.set(self.countries)
        FinalAdviceFactory(
            user=self.gov_user,
            team=self.team,
            case=self.case,
            goods_type=self.approved_goods_type,
            type=AdviceType.APPROVE,
        )
        FinalAdviceFactory(
            user=self.gov_user,
            team=self.team,
            case=self.case,
            goods_type=self.refused_goods_type,
            type=AdviceType.REFUSE,
        )
        FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=self.case, country=self.approved_country, type=AdviceType.APPROVE
        )
        FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=self.case, country=self.refused_country, type=AdviceType.REFUSE
        )

    def test_get_required_decisions(self):
        GoodCountryDecisionFactory(
            case=self.case, goods_type=self.approved_goods_type, country=self.countries[0], approve=True
        )
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        # Only one goods type has an approved combination
        # Both have a refused combination
        self.assertEqual(len(response_data["approved"]), 1)
        self.assertEqual(len(response_data["refused"]), 2)

        # Check approved combination
        self.assertEqual(response_data["approved"][0]["id"], str(self.approved_goods_type.id))
        self.assertEqual(response_data["approved"][0]["decision"], AdviceType.APPROVE)
        self.assertEqual(response_data["approved"][0]["control_list_entries"], AdviceType.APPROVE)

        y = 1

    def test_def(self):
        x = get_required_good_type_to_country_combinations(self.case.id)
        y = 1
