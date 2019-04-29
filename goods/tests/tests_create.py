from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from rest_framework.reverse import reverse
from django.urls import path, include

from test_helpers.org_and_user_helper import OrgAndUserHelper


class OrganisationTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('goods/', include('goods.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_create_new_good(self):
        data = {'description': 'a good',
                'control_code': 'ML1a',
                'is_good_controlled': 'True',
                'is_good_end_product': 'True'}

        url = reverse('goods:goods')
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEquals(response.status_code, 201)

    def test_fail_create_new_good(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': '', 'is_good_end_product': ''}
        url = reverse('goods:goods')
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEquals(response.status_code, 400)