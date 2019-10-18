from rest_framework import status
from rest_framework.reverse import reverse

from goodstype.models import GoodsType
from test_helpers.clients import DataTestClient


class GoodsTypeOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse('goodstype:goodstypes-list')
        self.open_application = self.create_open_application(self.organisation)
        self.data = {
            'description': 'Widget',
            'is_good_controlled': True,
            'control_code': 'ML1a',
            'is_good_end_product': True,
            'application': self.open_application.pk
        }

    def test_create_goodstype_on_open_application_as_exporter_user_success(self):
        response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()['good']
        self.assertEquals(response_data['description'], 'Widget')
        self.assertEquals(response_data['is_good_controlled'], True)
        self.assertEquals(response_data['control_code'], 'ML1a')
        self.assertEquals(response_data['is_good_end_product'], True)

    def test_create_goodstype_on_open_application_as_gov_user_failure(self):
        response = self.client.post(self.url, self.data, **self.gov_headers)

        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_goodstype_on_standard_application_as_exporter_user_failure(self):
        application = self.create_standard_application(self.organisation)

        data = {
            'description': 'Widget',
            'is_good_controlled': True,
            'control_code': 'ML1a',
            'is_good_end_product': True,
            'application': application.pk
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_goodstype_from_open_application_as_exporter_user_success(self):
        self.create_open_application(self.organisation)
        all_goods_types = GoodsType.objects.all()
        goods_type_id = all_goods_types.first().id
        initial_goods_types_count = all_goods_types.count()
        url = reverse('goodstype:goodstypes_detail', kwargs={'pk': goods_type_id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEquals(GoodsType.objects.all().count(), initial_goods_types_count - 1)
