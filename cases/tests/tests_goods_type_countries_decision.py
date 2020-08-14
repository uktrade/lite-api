from django.db.models import Q
from django.urls import reverse
from rest_framework import status

from cases.enums import AdviceType
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import GoodCountryDecision, Advice
from cases.tests.factories import FinalAdviceFactory, GoodCountryDecisionFactory
from api.conf.constants import GovPermissions
from api.goodstype.tests.factories import GoodsTypeFactory
from lite_content.lite_api.strings import Cases
from static.control_list_entries.models import ControlListEntry
from static.countries.models import Country
from test_helpers.clients import DataTestClient


class GoodsCountriesDecisionsTests(DataTestClient):
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
        self.approved_goods_type_clcs = [ControlListEntry.objects.first()]
        self.approved_goods_type.control_list_entries.set(self.approved_goods_type_clcs)
        self.approved_goods_type.countries.set(self.countries)
        self.refused_goods_type = GoodsTypeFactory(application=self.case)
        self.refused_goods_type_clcs = [ControlListEntry.objects.last()]
        self.refused_goods_type.control_list_entries.set(self.refused_goods_type_clcs)
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

    def _assert_goods_type(self, data, goods_type, decision, clcs):
        self.assertEqual(data["id"], str(goods_type.id))
        self.assertEqual(data["decision"], decision)
        self.assertEqual(data["description"], goods_type.description)
        self.assertEqual(data["control_list_entries"], [{"rating": clc.rating, "text": clc.text} for clc in clcs])

    def _assert_country(self, data, country, decision):
        self.assertEqual(data["id"], str(country.id))
        self.assertEqual(data["decision"], decision)
        self.assertEqual(data["name"], country.name)

    def test_get_required_goods_countries_decisions(self):
        GoodCountryDecisionFactory(
            case=self.case, goods_type=self.approved_goods_type, country=self.approved_country, approve=True
        )
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Only one goods type has an approved combination
        # Both have a refused combination
        self.assertEqual(len(response_data["approved"]), 1)
        self.assertEqual(len(response_data["refused"]), 2)

        # Check approved combination
        self._assert_goods_type(
            response_data["approved"][0], self.approved_goods_type, AdviceType.APPROVE, self.approved_goods_type_clcs
        )
        # Only one country for this goods type was approved
        self.assertEqual(len(response_data["approved"][0]["countries"]), 1)
        self._assert_country(response_data["approved"][0]["countries"][0], self.approved_country, AdviceType.APPROVE)
        # Check existing answer is populated
        self.assertEqual(response_data["approved"][0]["countries"][0]["value"], AdviceType.APPROVE)

        # Check refused combinations
        self._assert_goods_type(
            response_data["refused"][0], self.approved_goods_type, AdviceType.APPROVE, self.approved_goods_type_clcs
        )
        # Only one country for this goods type was refused
        self.assertEqual(len(response_data["refused"][0]["countries"]), 1)
        self._assert_country(response_data["refused"][0]["countries"][0], self.refused_country, AdviceType.REFUSE)

        self._assert_goods_type(
            response_data["refused"][1], self.refused_goods_type, AdviceType.REFUSE, self.refused_goods_type_clcs
        )
        # Both countries should appear as the goods type is refused
        self.assertEqual(len(response_data["refused"][1]["countries"]), 2)
        self._assert_country(response_data["refused"][1]["countries"][0], self.approved_country, AdviceType.APPROVE)
        self._assert_country(response_data["refused"][1]["countries"][1], self.refused_country, AdviceType.REFUSE)

    def test_get_required_goods_countries_decisions_with_provisos(self):
        # Update advice to proviso
        Advice.objects.filter(Q(goods_type=self.approved_goods_type) | Q(country=self.approved_country)).update(
            type=AdviceType.PROVISO
        )

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response_data["approved"]), 1)
        self._assert_goods_type(
            response_data["approved"][0], self.approved_goods_type, AdviceType.PROVISO, self.approved_goods_type_clcs
        )
        self.assertEqual(len(response_data["approved"][0]["countries"]), 1)
        self._assert_country(response_data["approved"][0]["countries"][0], self.approved_country, AdviceType.PROVISO)

    def test_goods_countries_decisions_missing_decision_failure(self):
        response = self.client.post(self.url, **self.gov_headers, data={})
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["errors"],
            {f"{self.approved_goods_type.id}.{self.approved_country.id}": [Cases.GoodCountryMatrix.MISSING_ITEM]},
        )

    def test_goods_countries_decisions_success(self):
        data = {f"{self.approved_goods_type.id}.{self.approved_country.id}": "approve"}

        response = self.client.post(self.url, **self.gov_headers, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response_data["good_country_decisions"], [f"{self.approved_goods_type.id}.{self.approved_country.id}"],
        )
        self.assertEqual(
            GoodCountryDecision.objects.filter(
                case=self.case, goods_type=self.approved_goods_type, country=self.approved_country, approve=True
            ).count(),
            1,
        )

    def test_goods_countries_decisions_overwrite_success(self):
        template = self.create_letter_template(case_types=[self.case.case_type])
        self.create_generated_case_document(
            case=self.case, template=template, advice_type=AdviceType.APPROVE, visible_to_exporter=False
        )
        GoodCountryDecisionFactory(
            case=self.case, goods_type=self.approved_goods_type, country=self.approved_country, approve=True
        )
        data = {f"{self.approved_goods_type.id}.{self.approved_country.id}": "refuse"}

        response = self.client.post(self.url, **self.gov_headers, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response_data["good_country_decisions"], [f"{self.approved_goods_type.id}.{self.approved_country.id}"],
        )
        self.assertEqual(
            GoodCountryDecision.objects.filter(
                case=self.case, goods_type=self.approved_goods_type, country=self.approved_country, approve=False
            ).count(),
            1,
        )
        # Check existing case documents are removed
        self.assertFalse(GeneratedCaseDocument.objects.filter(case=self.case).exists())
