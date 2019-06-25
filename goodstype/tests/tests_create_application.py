from parameterized import parameterized
from rest_framework import status
from django.contrib.contenttypes.models import ContentType
from applications.models import Application
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class GoodsTypeCreateApplicationTests(DataTestClient):

    url = reverse('goodstype:goodstypes-list')

    @parameterized.expand([
        ('Widget', True, 'ML1a', True),  # Create a new goodtype successfully
    ])
    def test_create_goodstype(self,
                              description,
                              is_good_controlled,
                              control_code,
                              is_good_end_product,
                              application=False):
        if not application:
            application = Application.objects.create(name='test', licence_type='open_licence', export_type='temporary')

        data = {
            'description': description,
            'is_good_controlled': is_good_controlled,
            'control_code': control_code,
            'is_good_end_product': is_good_end_product,
            #'content_type': ContentType.objects.get(model='application').id,
            'object_id': application.pk
        }

        response = self.client.post(self.url, data, **self.headers)

        if response.status_code == status.HTTP_201_CREATED:
            response_data = response.json()['good']
            self.assertEquals(response_data['content_type_name'], 'application')
            self.assertEquals(response_data['content_object']['licence_type'], application.licence_type)
            self.assertEquals(response_data['description'], description)
            self.assertEquals(response_data['is_good_controlled'], is_good_controlled)
            self.assertEquals(response_data['control_code'], control_code)
            self.assertEquals(response_data['is_good_end_product'], is_good_end_product)
