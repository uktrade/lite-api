from rest_framework import status
from rest_framework import status
from rest_framework.reverse import reverse

from applications.models import OpenApplication, StandardApplication
from test_helpers.clients import DataTestClient


class GoodsTypeCreateDraftTests(DataTestClient):
    url = reverse('goodstype:goodstypes-list')

    def test_create_goodstype_on_open_application(self):
        draft = OpenApplication.objects.create(name='test', licence_type='open_licence', export_type='temporary',
                                               have_you_been_informed=False)

        data = {
            'description': 'Widget',
            'is_good_controlled': True,
            'control_code': 'ML1a',
            'is_good_end_product': True,
            'application': draft.pk
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()['good']
        self.assertEquals(response_data['description'], 'Widget')
        self.assertEquals(response_data['is_good_controlled'], True)
        self.assertEquals(response_data['control_code'], 'ML1a')
        self.assertEquals(response_data['is_good_end_product'], True)

    def test_create_goodstype_on_standard_application_failure(self):
        draft = StandardApplication.objects.create(name='test',
                                                   licence_type='standard_licence',
                                                   export_type='temporary',
                                                   have_you_been_informed=False)

        data = {
            'description': 'Widget',
            'is_good_controlled': True,
            'control_code': 'ML1a',
            'is_good_end_product': True,
            'application': draft.pk
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
