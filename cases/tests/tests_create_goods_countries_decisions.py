from django.urls import reverse
from rest_framework import status

from cases.models import Case
from drafts.models import CountryOnDraft
from goodstype.models import GoodsType
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class CreateGoodsCountriesDecisions(DataTestClient):

    def setUp(self):
        super().setUp()
        self.open_draft = self.create_open_draft(self.organisation)

        self.goods_types = GoodsType.objects.filter(object_id=self.open_draft.id)
        self.goods_type_1 = self.goods_types[0]
        self.goods_type_2 = self.goods_types[1]

        # Add a country to the draft
        self.country_1 = get_country('ES')
        self.country_2 = get_country('US')
        self.country_3 = get_country('FR')

        self.all_countries = [self.country_1, self.country_2, self.country_3]
        for country in self.all_countries:
            CountryOnDraft(draft=self.open_draft, country=country).save()

        application = self.submit_draft(self.open_draft)
        self.case = Case.objects.get(application=application)

        self.goods_countries_url = reverse('cases:goods_countries_decisions', kwargs={'pk': self.case.id})

    def test_make_goods_countries_decisions_success(self):
        data = {'good_countries':
            [
                {'good': '58b63f71-943c-4b24-8497-b4480d1e7580', 'country': 'ZM', 'advice_type': 'Approve', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                {'good': '58b63f71-943c-4b24-8497-b4480d1e7580', 'country': 'LR', 'advice_type': 'Refuse', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                {'good': '58b63f71-943c-4b24-8497-b4480d1e7580', 'country': 'AL', 'advice_type': 'No Licence Required', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                {'good': '566e6af6-90af-4496-8b83-f639a1346b55', 'country': 'BW', 'advice_type': 'Approve', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                {'good': '566e6af6-90af-4496-8b83-f639a1346b55', 'country': 'DE', 'advice_type': 'Approve', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                {'good': '566e6af6-90af-4496-8b83-f639a1346b55', 'country': 'SC', 'advice_type': 'Approve', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                {'good': '27e73af3-6faf-45e6-8877-5138c446c311', 'country': 'DE', 'advice_type': 'Approve', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                {'good': '27e73af3-6faf-45e6-8877-5138c446c311', 'country': 'AI', 'advice_type': 'Refuse', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                {'good': '27e73af3-6faf-45e6-8877-5138c446c311', 'country': 'BW', 'advice_type': 'Refuse', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
            ]}

        response = self.client.post(self.goods_countries_url, data, **self.gov_headers)

        print(response.json()['data']['good_countries'])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']['good_countries']), 9)

    def test_goods_countries_multiple_decisions_same_good_country_combination_failure(self):
        data = {'good_countries':
            [
                {'good': '58b63f71-943c-4b24-8497-b4480d1e7580', 'country': 'ZM', 'advice_type': 'Approve', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                {'good': '58b63f71-943c-4b24-8497-b4480d1e7580', 'country': 'ZM', 'advice_type': 'Refuse', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
            ]
        }

        response = self.client.post(self.goods_countries_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
