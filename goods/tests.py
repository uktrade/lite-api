from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from rest_framework.reverse import reverse
from django.urls import path, include

from drafts.tests import DraftTestHelpers
from goods.models import Good
from goods.serializers import GoodSerializer


class OrganisationTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('goods/', include('goods.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = DraftTestHelpers(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    # Creation

    def test_create_new_good(self):
        data = {'description': 'a good',
                'control_code': 'ML1a',
                'is_good_controlled': 'True',
                'is_good_end_product': 'True'}

        url = reverse('goods:goods')
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEquals(response.status_code, 201)

    def test_fail_create_new_good(self):
        data = { 'description': '', 'control_code': '', 'is_good_controlled': '', 'is_good_end_product': '' }
        url = reverse('goods:goods')
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEquals(response.status_code, 400)

    # Serializers

    def test_serializer_validation_with_empty(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': '', 'is_good_end_product': ''}
        serializer = GoodSerializer(data=data)
        serializer.is_valid()
        self.assertIsNotNone(serializer.errors['description'])
        self.assertIsNotNone(serializer.errors['is_good_controlled'])
        self.assertIsNotNone(serializer.errors['is_good_end_product'])

    def test_serializer_validation_with_controlled(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': 'True', 'is_good_end_product': ''}
        serializer = GoodSerializer(data=data)
        serializer.is_valid()
        self.assertIsNotNone(serializer.errors['description'])
        self.assertIsNotNone(serializer.errors['control_code'])
        self.assertIsNotNone(serializer.errors['is_good_end_product'])

    def test_serializer_validation_with_decontrolled(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': 'False', 'is_good_end_product': ''}
        serializer = GoodSerializer(data=data)
        serializer.is_valid()
        self.assertIsNotNone(serializer.errors['description'])
        self.assertNotIn('control_code', serializer.errors)
        self.assertIsNotNone(serializer.errors['is_good_end_product'])

    # View

    def test_view_good_details(self):
        good = Good(description='thing',
                    is_good_controlled=False,
                    is_good_end_product=True,
                    organisation=self.test_helper.organisation)
        good.save()

        url = reverse('goods:good', kwargs={'pk': good.id})
        response = self.client.get(url, **{'HTTP_USER_ID': str(self.test_helper.user.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fail_view_other_organisations_goods_dtails(self):
        test_helper_2 = DraftTestHelpers(name='organisation2')

        good = Good(description='thing',
                    is_good_controlled=False,
                    is_good_end_product=True,
                    organisation=self.test_helper.organisation)
        good.save()

        url = reverse('goods:good', kwargs={'pk': good.id})
        response = self.client.get(url, **{'HTTP_USER_ID': str(test_helper_2.user.id)})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
