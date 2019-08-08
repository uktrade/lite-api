from rest_framework import status
from rest_framework.reverse import reverse

from applications.models import Application
from gov_users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient


class GoodViewTests(DataTestClient):

    def test_view_goodstype_details(self):
        application = Application.objects.create(name='test', licence_type='open_licence', export_type='temporary')
        goods_type = self.create_goods_type(content_type_model='application', obj=application)

        url = reverse('goodstype:goodstypes-detail', kwargs={'pk': goods_type.id})
        response = self.client.get(url, **{'HTTP_EXPORTER_USER_TOKEN': user_to_token(self.test_helper.user)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
