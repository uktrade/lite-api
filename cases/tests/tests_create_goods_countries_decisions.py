from django.urls import reverse
from rest_framework import status

from applications.models import CountryOnApplication
from cases.models import GoodCountryDecision
from conf import constants
from goodstype.models import GoodsType
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient
from users.models import Role


class CreateGoodsCountriesDecisions(DataTestClient):
    def setUp(self):
        super().setUp()
        self.open_draft = self.create_draft_open_application(self.organisation)

        role = Role(name="team_level")
        role.permissions.set(
            [
                constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
                constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
            ]
        )
        role.save()

        self.gov_user.role = role
        self.gov_user.save()

        self.goods_types = GoodsType.objects.filter(application=self.open_draft.id)
        self.goods_type_1 = self.goods_types[0]
        self.goods_type_2 = self.goods_types[1]

        # Add a country to the draft
        CountryOnApplication(application=self.open_draft, country=get_country("US")).save()

        self.case = self.submit_application(self.open_draft)

        self.goods_countries_url = reverse("cases:goods_countries_decisions", kwargs={"pk": self.case.id})

    def test_make_goods_countries_decisions_success(self):
        data = {
            "good_countries": [
                {"good": str(self.goods_type_1.id), "country": "US", "decision": "approve", "case": str(self.case.id)},
                {"good": str(self.goods_type_2.id), "country": "US", "decision": "approve", "case": str(self.case.id)},
            ]
        }

        response = self.client.post(self.goods_countries_url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GoodCountryDecision.objects.count(), len(data["good_countries"]))
        self.assertEqual(len(response.json()["data"]), len(data["good_countries"]))

    def test_saving_overwrites_previous_assignment(self):
        self.create_good_country_decision(self.case, self.goods_type_1, get_country("US"), "approve")

        data = {
            "good_countries": [
                {"good": str(self.goods_type_1.id), "country": "US", "decision": "refuse", "case": str(self.case.id),}
            ]
        }

        self.client.post(self.goods_countries_url, data, **self.gov_headers)

        self.assertEqual(GoodCountryDecision.objects.count(), 1)
