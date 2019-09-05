from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodControlled
from test_helpers.clients import DataTestClient


class GoodsCreateTests(DataTestClient):

    url = reverse('goods:goods')

    @parameterized.expand([
        ('Widget', GoodControlled.YES, 'ML1a', True, '1337', status.HTTP_201_CREATED),  # Create a new good
        # successfully
        ('Widget', GoodControlled.NO, '', True, '1337', status.HTTP_201_CREATED),  # Control Code shouldn't be set
        ('Test Unsure Good Name', GoodControlled.UNSURE, '', True, '1337', status.HTTP_201_CREATED),  # CLC query
        ('Widget', GoodControlled.YES, '', True, '1337', status.HTTP_400_BAD_REQUEST),  # Controlled but is missing
        # control code
        ('', '', '', '', '', status.HTTP_400_BAD_REQUEST),  # Request is empty
    ])
    def test_create_good(self,
                         description,
                         is_good_controlled,
                         control_code,
                         is_good_end_product,
                         part_number,
                         expected_status):
        # Assemble
        data = {
            'description': description,
            'is_good_controlled': is_good_controlled,
            'control_code': control_code,
            'is_good_end_product': is_good_end_product,
            'part_number': part_number
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEquals(response.status_code, expected_status)

        if response.status_code == status.HTTP_201_CREATED:
            response_data = response.json()['good']
            self.assertEquals(response_data['description'], description)
            self.assertEquals(response_data['is_good_controlled'], is_good_controlled)
            self.assertEquals(response_data['control_code'], control_code)
            self.assertEquals(response_data['is_good_end_product'], is_good_end_product)
            self.assertEquals(response_data['part_number'], part_number)
