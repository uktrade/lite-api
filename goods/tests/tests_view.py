from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodControlled
from goods.models import Good
from users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient
from users.libraries.get_user import get_users_from_organisation


class GoodViewTests(DataTestClient):

    def test_view_good_details(self):
        good = Good(description='thing',
                    is_good_controlled=GoodControlled.NO,
                    is_good_end_product=True,
                    organisation=self.organisation)
        good.save()

        url = reverse('goods:good', kwargs={'pk': good.id})
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fail_view_other_organisations_goods_details(self):
        organisation_2 = self.create_organisation()
        organisation_2_admin = get_users_from_organisation(organisation_2)[0]

        good = Good(description='thing',
                    is_good_controlled=GoodControlled.NO,
                    is_good_end_product=True,
                    organisation=self.organisation)
        good.save()

        url = reverse('goods:good', kwargs={'pk': good.id})
        response = self.client.get(url, **{'HTTP_EXPORTER_USER_TOKEN': user_to_token(organisation_2_admin), 'HTTP_ORGANISATION_ID': str(organisation_2.id)})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_good__query_filter_by_description(self):
        org = self.organisation

        self.create_controlled_good('thing1', org)
        self.create_controlled_good('Thing2', org)
        self.create_controlled_good('item3', org)

        url = reverse('goods:goods') + '?description=thing'
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()['goods']
        self.assertEqual(len(response_data), 2)

        url = reverse('goods:goods') + '?description=item'
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()['goods']
        self.assertEqual(len(response_data), 1)

        url = reverse('goods:goods')
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()['goods']
        self.assertEqual(len(response_data), 3)

    def test_view_good__query_filter_by_part_number_and_combinations(self):
        org = self.organisation

        # create a set of Goods for the test
        Good.objects.create(description='car1',
                            is_good_controlled=GoodControlled.YES,
                            control_code='ML1',
                            is_good_end_product=True,
                            part_number='cl500',
                            organisation=org)

        Good.objects.create(description='Car2',
                            is_good_controlled=GoodControlled.YES,
                            control_code='ML1',
                            is_good_end_product=True,
                            part_number='CL300',
                            organisation=org)

        Good.objects.create(description='car3',
                            is_good_controlled=GoodControlled.YES,
                            control_code='ML1',
                            is_good_end_product=True,
                            part_number='ML500',
                            organisation=org)

        Good.objects.create(description='Truck',
                            is_good_controlled=GoodControlled.YES,
                            control_code='ML1',
                            is_good_end_product=True,
                            part_number='CL1000',
                            organisation=org)

        url = reverse('goods:goods') + '?part_number=cl'
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["goods"]
        self.assertEqual(len(response_data), 3)

        url = reverse('goods:goods') + '?part_number=100'
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["goods"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['description'], 'Truck')

        url = reverse('goods:goods') + '?part_number=cl&description=car'
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["goods"]
        self.assertEqual(len(response_data), 2)

    @parameterized.expand([
        ('ML3', 2),
        ('ML3a', 1),
    ])
    def test_view_good__query_filter_by_control_rating(self, control_rating, size):
        org = self.organisation

        self.create_controlled_good('thing1', org, 'ML3a')
        self.create_controlled_good('Thing2', org, 'ML3b')
        self.create_controlled_good('item3', org, 'ML4')

        url = reverse('goods:goods') + '?control_rating=' + control_rating

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()['goods']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), size)
