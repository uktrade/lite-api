from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from rest_framework.reverse import reverse
from django.urls import path, include
from goods.serializers import GoodSerializer


class OrganisationTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('goods/', include('goods.urls'))
    ]

    client = APIClient

    def test_create_new_good(self):
        data = {'description': 'a good',
                'control_code': 'ML1a',
                'is_good_controlled': 'True',
                'is_good_end_product': 'True'}

        url = reverse('goods:goods')
        response = self.client.post(url, data, format='json')
        self.assertEquals(response.status_code, 201)

    def test_fail_create_new_good(self):
        data = { 'description': '', 'control_code': '', 'is_good_controlled': '', 'is_good_end_product': '' }
        url = reverse('goods:goods')
        response = self.client.post(url, data, format='json')
        self.assertEquals(response.status_code, 400)

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
