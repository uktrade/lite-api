from django.urls import reverse

from cases.enums import AdviceType, AdviceLevel
from cases.libraries.get_goods_type_countries_decisions import good_type_to_country_decisions
from cases.tests.factories import FinalAdviceFactory
from goodstype.tests.factories import GoodsTypeFactory
from static.countries.models import Country
from test_helpers.clients import DataTestClient


class FinaliseCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_open_application_case(self.organisation)
        self.url = reverse("cases:goods_countries_decisions", kwargs={"pk": self.case.id})
        countries = [Country.objects.first(), Country.objects.last()]
        self.approved_goods_type = GoodsTypeFactory(application=self.case)
        self.approved_goods_type.countries.set(countries)
        self.refused_goods_type = GoodsTypeFactory(application=self.case)
        self.refused_goods_type.countries.set(countries)
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
            user=self.gov_user, team=self.team, case=self.case, country=countries[0], type=AdviceType.APPROVE
        )
        FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=self.case, country=countries[1], type=AdviceType.REFUSE
        )

    def test_abc(self):
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        y = 1
