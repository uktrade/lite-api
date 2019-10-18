from rest_framework import status
from rest_framework.reverse import reverse

from goodstype.models import GoodsType
from test_helpers.clients import DataTestClient


class GoodViewTests(DataTestClient):

    def test_view_goodstype_details(self):
        application = self.create_open_application(self.organisation)
        goods_type = GoodsType.objects.filter(application=application).first()
        url = reverse('goodstype:goodstypes_detail', kwargs={'pk': goods_type.id})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
