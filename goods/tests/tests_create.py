from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from cases.models import Case
from goods.enums import GoodControlled
from goods.models import Good
from test_helpers.clients import DataTestClient


class GoodsCreateTests(DataTestClient):

    url = reverse('goods:goods')

    @parameterized.expand([
        ('Widget', GoodControlled.YES, 'ML1a', True, '1337', status.HTTP_201_CREATED, ''),  # Create a new good
        # successfully
        ('Widget', GoodControlled.NO, '', True, '1337', status.HTTP_201_CREATED, ''),  # Control Code shouldn't be set
        ('Test Unsure Good Name', GoodControlled.UNSURE, '', True, '1337', status.HTTP_201_CREATED, 'This is test text'),  # CLC query
        ('Widget', GoodControlled.YES, '', True, '1337', status.HTTP_400_BAD_REQUEST, ''),  # Controlled but is missing
        # control code
        ('', '', '', '', '', status.HTTP_400_BAD_REQUEST, ''),  # Request is empty
    ])
    def test_create_good(self,
                         description,
                         is_good_controlled,
                         control_code,
                         is_good_end_product,
                         part_number,
                         expected_status,
                         not_sure_details_details):
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

            self.create_good_document(good=Good.objects.get(id=response_data['id']),
                                      user=self.exporter_user,
                                      organisation=self.organisation,
                                      name='doc1',
                                      s3_key='doc3')

            if is_good_controlled == GoodControlled.UNSURE:
                data = {
                    'not_sure_details_details': not_sure_details_details,
                    'not_sure_details_control_code': 'ML17b',
                    'good_id': response_data['id']
                }

                url = reverse('applications:clcs')
                response = self.client.post(url, data, **self.exporter_headers)

                self.assertEquals(response.status_code, expected_status)

        # Assert
        if is_good_controlled == GoodControlled.UNSURE:
            case = Case.objects.get()
            # If a good is an 'unsure' good, then a case should have been created with a clc query and the clc query's good should be
            # the good that was created.
            self.assertEqual(case.query.good.description, description)
