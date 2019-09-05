from django.urls import reverse
from rest_framework import status

from goods.enums import GoodControlled
from goods.models import Good
from queries.control_list_classifications.models import ControlListClassificationQuery
from test_helpers.clients import DataTestClient


class ControlListClassificationsQueryCreateTests(DataTestClient):

    url = reverse('queries:control_list_classifications:control_list_classifications')

    def test_create_control_list_classification_query(self):
        good = Good(description='Good description',
                    is_good_controlled=GoodControlled.UNSURE,
                    control_code='ML1',
                    is_good_end_product=True,
                    part_number='123456',
                    organisation=self.organisation)
        good.save()

        data = {
            'good_id': good.id,
            'not_sure_details_control_code': 'ML1a',
            'not_sure_details_details': 'I don\'t know',
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['id'], ControlListClassificationQuery.objects.get().id)
