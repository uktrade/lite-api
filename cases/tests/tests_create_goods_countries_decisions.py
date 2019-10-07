from django.urls import reverse
from rest_framework import status

from cases.models import Case, GoodCountryDecision
from conf.constants import Permissions
from applications.models import CountryOnApplication
from goodstype.models import GoodsType
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient
from users.models import Role


class CreateGoodsCountriesDecisions(DataTestClient):

    def setUp(self):
        super().setUp()
        self.open_draft = self.create_open_draft(self.organisation)

        role = Role(name='team_level')
        role.permissions.set([Permissions.MANAGE_FINAL_ADVICE, Permissions.MANAGE_TEAM_ADVICE])
        role.save()

        self.gov_user.role = role
        self.gov_user.save()

        self.goods_types = GoodsType.objects.filter(application=self.open_draft.id)
        self.goods_type_1 = self.goods_types[0]
        self.goods_type_2 = self.goods_types[1]

        # Add a country to the draft
        self.country_1 = get_country('ES')
        self.country_2 = get_country('US')
        self.country_3 = get_country('FR')

        self.all_countries = [self.country_1, self.country_2, self.country_3]
        for country in self.all_countries:
            CountryOnApplication(application=self.open_draft, country=country).save()

        application = self.submit_draft(self.open_draft)
        self.case = Case.objects.get(application=application)

        self.goods_countries_url = reverse('cases:goods_countries_decisions', kwargs={'pk': self.case.id})

    def test_make_goods_countries_decisions_success(self):
        data = {'good_countries':
            [
                {'good': str(self.goods_type_1.id), 'country': 'ZM', 'decision': 'approve', 'case': str(self.case.id)},
                {'good': str(self.goods_type_1.id), 'country': 'LR', 'decision': 'refuse', 'case': str(self.case.id)},
                {'good': str(self.goods_type_1.id), 'country': 'AL', 'decision': 'no_licence_required',
                 'case': str(self.case.id)},
                {'good': str(self.goods_type_2.id), 'country': 'BW', 'decision': 'approve', 'case': str(self.case.id)},
                {'good': str(self.goods_type_2.id), 'country': 'DE', 'decision': 'approve', 'case': str(self.case.id)},
                {'good': str(self.goods_type_2.id), 'country': 'SC', 'decision': 'approve', 'case': str(self.case.id)},
            ]}

        response = self.client.post(self.goods_countries_url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GoodCountryDecision.objects.count(), len(data['good_countries']))
        self.assertEqual(len(response.json()['data']), len(data['good_countries']))

    def test_saving_overwrites_previous_assignment(self):
        self.create_good_country_decision(self.case, self.goods_type_1, self.country_1, 'approve')

        data = {
            'good_countries': [
                {
                    'good': str(self.goods_type_1.id),
                    'country': str(self.country_1.id),
                    'decision': 'refuse',
                    'case': str(self.case.id)
                }
            ]
        }

        self.client.post(self.goods_countries_url, data, **self.gov_headers)

        self.assertEqual(GoodCountryDecision.objects.count(), 1)
