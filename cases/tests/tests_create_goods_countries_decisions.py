from django.urls import reverse

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

        self.good_url = reverse('goodstype:goodstypes_detail', kwargs={'pk': self.goods_type_1.id})
        self.good_country_url = reverse('goodstype:assign_countries')

    def test_make_goods_countries_decisions_success(self):
        data = {'good_countries':
                [
                    {'good': '58b63f71-943c-4b24-8497-b4480d1e7580', 'country': 'ZM', 'advice_type': 'Proviso', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                    {'good': '58b63f71-943c-4b24-8497-b4480d1e7580', 'country': 'LR', 'advice_type': 'Refuse', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                    {'good': '58b63f71-943c-4b24-8497-b4480d1e7580', 'country': 'AL', 'advice_type': 'No Licence Required', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                    {'good': '566e6af6-90af-4496-8b83-f639a1346b55', 'country': 'BW', 'advice_type': 'Approve', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                    {'good': '566e6af6-90af-4496-8b83-f639a1346b55', 'country': 'DE', 'advice_type': 'Approve', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                    {'good': '566e6af6-90af-4496-8b83-f639a1346b55', 'country': 'SC', 'advice_type': 'Proviso', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                    {'good': '27e73af3-6faf-45e6-8877-5138c446c311', 'country': 'DE', 'advice_type': 'Approve', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                    {'good': '27e73af3-6faf-45e6-8877-5138c446c311', 'country': 'AI', 'advice_type': 'Refuse', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                    {'good': '27e73af3-6faf-45e6-8877-5138c446c311', 'country': 'BW', 'advice_type': 'Refuse', 'case': 'cc051e5a-fb32-428a-bd07-bf2de585e193'},
                ]}
        self.assertTrue(False)
