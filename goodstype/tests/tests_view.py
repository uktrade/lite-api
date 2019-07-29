from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse

from applications.models import Application
from goodstype.models import GoodsType
from gov_users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient


class GoodViewTests(DataTestClient):

    def create_goods_type(self, content_type_model, obj):
        goodstype = GoodsType(description='thing',
                              is_good_controlled=False,
                              control_code='ML1a',
                              is_good_end_product=True,
                              content_type=ContentType.objects.get(model=content_type_model),
                              object_id=obj.pk,
                              )
        goodstype.save()
        return goodstype


    def test_view_goodstype_details(self):
        application = Application.objects.create(name='test', licence_type='open_licence', export_type='temporary')
        goodstype = self.create_goods_type(content_type_model='application', obj=application)

        url = reverse('goodstype:goodstypes-detail', kwargs={'pk': goodstype.id})
        response = self.client.get(url, **{'HTTP_EXPORTER_USER_TOKEN': user_to_token(self.test_helper.user)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
