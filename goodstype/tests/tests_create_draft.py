from parameterized import parameterized
from rest_framework import status
from django.contrib.contenttypes.models import ContentType
from drafts.models import Draft
from rest_framework.reverse import reverse
from test_helpers.clients import DataTestClient


class GoodsTypeCreateDraftTests(DataTestClient):

    url = reverse('goodstype:goodstypes-list')

    @parameterized.expand([
        ('Widget', True, 'ML1a', True),  # Create a new goodtype successfully
    ])
    def test_create_goodstype(self,
                              description,
                              is_good_controlled,
                              control_code,
                              is_good_end_product,
                              draft=False):
        if not draft:
            draft = Draft.objects.create(name='test', licence_type='open_licence', export_type='temporary')

        data = {
            'description': description,
            'is_good_controlled': is_good_controlled,
            'control_code': control_code,
            'is_good_end_product': is_good_end_product,
            'content_type': ContentType.objects.get(model='draft').id,
            'object_id': draft.pk
        }

        response = self.client.post(self.url, data, **self.headers)

        if response.status_code == status.HTTP_201_CREATED:
            response_data = response.json()['good']
            self.assertEquals(response_data['content_type_name'], 'draft')
            self.assertEquals(response_data['content_object']['licence_type'], draft.licence_type)
            self.assertEquals(response_data['description'], description)
            self.assertEquals(response_data['is_good_controlled'], is_good_controlled)
            self.assertEquals(response_data['control_code'], control_code)
            self.assertEquals(response_data['is_good_end_product'], is_good_end_product)
